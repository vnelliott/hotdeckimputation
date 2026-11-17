# %% 1. CONFIGURATION
# ==========================================================

# Reuse previously processed ABM data?
# 0 = Build from raw station files
# 1 = Load a previously saved sdata CSV
reuse_sdata = 1

# Range of years
syear = 1895
eyear = 2024

# Choose station network for donor pool
# 0 = Full network
# 1 = 30-year minimum network
# 2 = Sentinel network
network = 0

# Choose which stations to impute
# 0 = All stations in the selected network
# 1 = Sentinel stations only
impute_targets = 1

# Geographic bounds for station selection
# dlat and dlon are half-widths around the center
boxbds = {
    'clat': 37.2,
    'clon': -95.7,
    'dlat': 12.7,
    'dlon': 29.6
}

# Annual block maximum duration
interval = ['01d']

# Donor-selection method
# 0 = Antidistance
# 1 = RMSD
# 2 = PC Scores
# 3 = Bounded PC1 Distance
method = 0

# PCA explained-variance proportions
# Update to match the PCA results for the selected network.
# Used only for method = 2.
PC1 = 0.618822012410706
PC2 = 0.118309243866165
PC3 = 0.0972184973164955

# Generate donor-tracking files?
# 0 = No
# 1 = Yes
track = 1

# %% 2. DIRECTORIES/FILE PATHS
# ==========================================================

# Input station data
datadir = 'raw/'

# Donor network directories
networks = {
    0: 'GHCN-D',
    1: 'GHCN-D_30yrs',
    2: 'GHCN-D_sentinel'
}
dataext = networks[network]

# Filename tags for donor pool and imputation targets
pool_tags = {
    0: 'poolFull',
    1: 'pool30yr',
    2: 'poolSentinel'
}
target_tags = {
    0: 'targetsAll',
    1: 'targetsSentinel'
}

pool_tag = pool_tags[network]
target_tag = target_tags[impute_targets]

# Output filenames for each donor-selection method
output_names = {
    0: f'_bigbox_filled_ad_{pool_tag}_{target_tag}.csv',
    1: f'_bigbox_filled_rmsd_{pool_tag}_{target_tag}.csv',
    2: f'_bigbox_filled_pc_{pool_tag}_{target_tag}.csv',
    3: f'_bigbox_filled_boundedpc1_{pool_tag}_{target_tag}.csv'
}
framext = output_names[method]

# Output directories
framedir = 'frame/'
station_csv_dir = 'trackerfiles/'

# Filename identifier for donor-tracking files
tracker_base = framext.replace('_bigbox_filled_', '').replace('.csv', '')

# Sentinel station list
sentinel_csv = 'sentinelstations.csv'

# PCA scores for the selected donor network
pc_score_file = f'pca_scores_{networks[network]}.csv'

def get_sdata_filename(ival: str) -> str:
    """
    Build a unique sdata filename based on the interval, donor
    network, study period, and geographic bounds to prevent
    accidentally reusing data from a different configuration.
    """
    net_tag = networks[network]
    bbox_tag = (
        f"_{boxbds['clat']:.1f}N_{boxbds['clon']:.1f}E_"
        f"d{boxbds['dlat']:.1f}x{boxbds['dlon']:.1f}"
    )
    year_tag = f"_{syear}-{eyear}"
    
    return f"{ival}_{net_tag}{year_tag}{bbox_tag}_sdata.csv"

# %% 3. IMPORTS
# ==========================================================

import os
import csv
import time
from collections import defaultdict

import numpy as np
import pandas as pd
from geopy.distance import great_circle

# Record execution start time
start_time = time.time()

# %% 4. READING IN THE BLOCK MAXIMA DATA
# ==========================================================

class GHCN(object):
    """
    Iterator over station ABM CSV files in a directory.
    
    Each CSV is expected to contain:
        Column 0: Date (mm/dd/YYYY)
        Column 1: Annual block maximum precipitation
        Column 5: Station name
        Column 6: Latitude
        Column 7: Longitude
        Column 8: Elevation (may be blank)
    
    Yields:
        stnmeta: Dictionary containing station metadata
        stndata: List of date and precipitation value strings
    """
    def __init__(self, directory):
        self.directory = directory  # Initialize the directory attribute
        self.files = [f for f in os.listdir(directory) if f.endswith('.csv')]
        self.current_file_index = 0
        if not self.files:
            raise FileNotFoundError("No CSV files found in the specified directory.")
        self.open_next_file()

    def open_next_file(self):
        self.lines = open(os.path.join(self.directory, self.files[self.current_file_index]), "r")
        self.reader = csv.reader(self.lines)
        self.header = next(self.reader)  # Skip the header row

    def __iter__(self):
        return self

    def __next__(self):
        if self.reader is None:
            raise StopIteration
        try:
            stnmeta = {}
            first_data_row = next(self.reader)
            stnmeta['stid'] = os.path.splitext(self.files[self.current_file_index])[0]
            stnmeta['sname'] = first_data_row[5]  # Station name is in column F
            stnmeta['lat'] = float(first_data_row[6])  # Latitude is in column G
            stnmeta['lon'] = float(first_data_row[7])  # Longitude is in column H
            stnmeta['elev'] = float(first_data_row[8]) if first_data_row[8] else None  # Handle elevation

            stndata = []
            stndata.append(first_data_row[0] + '    ' + first_data_row[1])  # Add the first data row
            for row in self.reader:
                stndata.append(row[0] + '    ' + row[1])  # Combining date and precipitation data
            return stnmeta, stndata

        except StopIteration:
            self.lines.close()  # Close the current file
            self.current_file_index += 1
            if self.current_file_index < len(self.files):
                self.open_next_file()
                return self.__next__()
            else:
                raise StopIteration

        except ValueError as e:
            raise ValueError(f"Error processing file {self.files[self.current_file_index]}: {e}")

# %% 5. TRACKER FILES FUNCTIONS
# ==========================================================

def create_station_df(data):
    """
    Create a dataframe to track imputed data sources.
    
    Parameters:
    data : list : The data to include in the dataframe.
    
    Returns:
    pd.DataFrame : A DataFrame containing the tracking information.
    """
    # Define columns directly in the DataFrame creation
    columns = ["Year", "Value", "Donor", "Donor Lat", "Donor Lon", "Distance"]
    trackerdf = pd.DataFrame(data, columns=columns)
    return trackerdf  # Return the dataframe for further use


def update_station_df(year, data, donor_station, donor_lat, donor_lon, distance, trackerdf):
    """
    Update the tracker dataframe with new imputed data.

    Parameters:
    year : int : The year of the data.
    data : float : The imputed data value.
    donor_station : str : The station ID from which data was imputed.
    donor_lat : float : Latitude of the donor station.
    donor_lon : float : Longitude of the donor station.
    distance : float : Distance between the donor and receiving stations.
    trackerdf : pd.DataFrame : The existing dataframe for the station.

    Returns:
    trackerdf : pd.DataFrame : The updated dataframe.
    """
    new_row = pd.DataFrame({
        "Year": [year],
        "Value": [data],
        "Donor": [donor_station],
        "Donor Lat": [donor_lat],
        "Donor Lon": [donor_lon],
        "Distance": [distance]
    })

    if trackerdf.empty:
        trackerdf = new_row.copy()
    else:
        trackerdf = pd.concat([trackerdf, new_row], ignore_index=True)

    return trackerdf


def write_tracker_file(station_id, trackerdf, directory):
    """
    Save the station tracker dataframe to a CSV file.

    Parameters:
    station_id : str : The station ID.
    trackerdf : pd.DataFrame : The dataframe to be saved.
    directory : str : The directory to save the CSV.
    """
    tracker_fname = f"{tracker_base}__{station_id}.tracker.csv"
    trackerdf.to_csv(
        os.path.join(directory, tracker_fname),
        index=False
    )

# %% 6. CREATE SDATA
# ==========================================================

def dfob(ob, addto=None):
    """
    Create (or append to) a Pandas DataFrame with data from a station.
    
    Parameters:
    ob : tuple : A tuple containing station metadata and data.
    addto : pd.DataFrame : An existing DataFrame to append to.
    
    Returns:
    pd.DataFrame : The new or updated DataFrame with station data.
    """
    year = []
    precip = []
    
    stndata = ob[1]  # Data is in the second element of the tuple

    for data in stndata:
        parts = data.split()  # Splitting the string to extract year and precipitation
        date_obj = pd.to_datetime(parts[0], format='%m/%d/%Y')
        year.append(date_obj.year)
        precip.append(float(parts[1]))

    # Creating Start Dataframe
    sdat = pd.DataFrame({ob[0]['stid']: precip})
    sdat.index = year
    
    # Concatenating with existing DataFrame if addto is provided
    if addto is not None:
        sdat = pd.concat([addto, sdat], axis=1)
    
    return sdat

# %% 7. GREAT CIRCLE DISTANCE CALCULATION
# ==========================================================

dist_cache = defaultdict(dict)

def greatcircdist(stationlist,target,candidate):
    """
    Calculate the great-circle distance between two stations.
    
    Parameters:
    stationlist : dict : List of stations with their metadata.
    target : str : The target station ID.
    candidate : str : The candidate station ID.
    
    Returns:
    float : The great-circle distance in kilometers.
    """
    if candidate in dist_cache[target]: # since caches are stored both ways, only need one check
        return dist_cache[target][candidate]
    
    distance = great_circle((stationlist[target]['lat'],stationlist[target]['lon']),
                            (stationlist[candidate]['lat'],stationlist[candidate]['lon'])).km
    
    dist_cache[target][candidate] = distance
    dist_cache[candidate][target] = distance
    
    return distance

# %% 8. ANTIDISTANCE FUNCTIONS
# ==========================================================

def antidistance2(stationlist, target, candidate, weight):
    """
    Compute the distance between the desired station location and the candidate's location.
    
    Parameters:
    stationlist : dict : List of stations with their metadata.
    target : str : The target station ID.
    candidate : str : The candidate station ID.
    weight : int : The number of previous imputations for the target station.
    
    Returns:
    float : The squared distance from candidate station to optimal station location.
    """
    if track == 1:
        greatcircdist(stationlist,target,candidate)
    clat = np.cos(stationlist[target]['lat']*np.pi/180.)    # ratio of distance in degrees longitude to distance in degrees latitude
    antilat = (weight+1)*stationlist[target]['lat'] - weight*stationlist[target]['wlat']
    antilon = (weight+1)*stationlist[target]['lon'] - weight*stationlist[target]['wlon']
    dlat2 = (stationlist[candidate]['lat'] - antilat)**2
    dlon2 = ((stationlist[candidate]['lon'] - antilon)*clat)**2
    adist2 = dlat2 + dlon2    # Could use great circle distances but wouldn't matter much
    return adist2
    
def update_imputed_location(obmeta, targetstn, goodneighbor, count):
    """
    Update the mean geographic location of all donors previously
    used to impute the target.

    count = number of previous imputations for this target
    """
    obmeta[targetstn]['wlat'] = (
        obmeta[targetstn]['wlat'] * count
        + obmeta[goodneighbor]['lat']
    ) / (count + 1)

    obmeta[targetstn]['wlon'] = (
        obmeta[targetstn]['wlon'] * count
        + obmeta[goodneighbor]['lon']
    ) / (count + 1)
    
# %% 9. RMSD FUNCTIONS
# ==========================================================

if method == 1:
    rmsd_cache = defaultdict(dict)

def rmsd_distance(stationlist, sdata, target, candidate, radius):
    """
    Calculate the root mean square difference (RMSD) between
    two stations using their overlapping observed years.

    - Only considers candidates within the specified radius (km).
    - Caches calculated RMSD values for reuse.
    - Caches 'Nogood' when stations have no overlapping observations.
    - Always enforces the geographic radius, even when RMSD is cached.

    Returns:
    float : RMSD, or infinity if the candidate is outside the
            search radius or has no overlapping observations.
    """

    # Always enforce radius first (great-circle is cached in dist_cache)
    distance_km = greatcircdist(stationlist, target, candidate)
    if distance_km >= radius:
        return float('inf')

    # If RMSD is cached, return it (radius already enforced above)
    if candidate in rmsd_cache[target]:
        cached_value = rmsd_cache[target][candidate]
        if cached_value == 'Nogood':  # No common years
            return float('inf')
        return cached_value

    # Otherwise calculate RMSD using common years
    target_precip = sdata[target]
    candidate_precip = sdata[candidate]

    common_years = target_precip.dropna().index.intersection(candidate_precip.dropna().index)
    if common_years.empty:
        # No common data -> invalid for all radii
        rmsd_cache[target][candidate] = 'Nogood'
        rmsd_cache[candidate][target] = 'Nogood'
        return float('inf')

    # Restrict precipitation data to common years
    target_precip = target_precip.loc[common_years].values
    candidate_precip = candidate_precip.loc[common_years].values

    # Calculate RMSD and cache it
    rmsd = np.sqrt(np.mean((target_precip - candidate_precip) ** 2))
    rmsd_cache[target][candidate] = rmsd
    rmsd_cache[candidate][target] = rmsd

    return rmsd

# %% 10. PC SCORES FUNCTIONS
# ==========================================================

# Read PCA scores into dictionary
if method in (2, 3):
    pc_df = pd.read_csv(pc_score_file)
    pc_scores = {}
    for _, row in pc_df.iterrows():
        station_id = str(row['Station']).strip()
        # Remove '_1d' if present, to ensure consistency
        if station_id.endswith('_1d'):
            station_id = station_id[:-3]
        pc_scores[station_id] = [row['PC1'], row['PC2'], row['PC3']]
        
    pc_cache = defaultdict(dict)
    if method == 3:
        pc1_cache = defaultdict(dict)

def pc_score_distance(stationlist, target, candidate):
    """
    Compute the weighted distance between two stations in PC1-PC3 space,
    giving more weight to the PCs that explain more variance.
    """
    if track == 1:
        greatcircdist(stationlist, target, candidate)
        
    target = target.split('_')[0]
    candidate = candidate.split('_')[0]
    
    if candidate in pc_cache[target]:
        return pc_cache[target][candidate]
    
    target_vec = np.array(pc_scores[target])
    candidate_vec = np.array(pc_scores[candidate])
    
    # Explained variance weights from Section 1
    pc_weights = np.array([PC1, PC2, PC3])
    
    # Weighted Euclidean distance
    diff = target_vec - candidate_vec
    weighted_pc_dist = np.sqrt(np.sum(pc_weights * diff**2))
       
    # Store in cache both directions
    pc_cache[target][candidate] = weighted_pc_dist
    pc_cache[candidate][target] = weighted_pc_dist
    
    return weighted_pc_dist
        
def pc1_distance(stationlist, target, candidate, radius):
    """
    Calculate the absolute difference in PC1 scores between two
    stations within the specified geographic search radius (km).
    """
    distance_km = greatcircdist(stationlist, target, candidate)
    if distance_km >= radius:
        return float('inf')
    
    if candidate in pc1_cache[target]:
        return pc1_cache[target][candidate]

    target_id = target.split('_')[0]
    candidate_id = candidate.split('_')[0]

    dist = abs(pc_scores[target_id][0] - pc_scores[candidate_id][0])

    pc1_cache[target][candidate] = dist
    pc1_cache[candidate][target] = dist

    return dist

# %% 11. FINDING SUITABLE DONOR
# ==========================================================

def inbox(obloc, boxbds):
    yesinbox = False
    if boxbds['clat']-boxbds['dlat'] <= obloc['lat'] < boxbds['clat']+boxbds['dlat']:
        if boxbds['clon']-boxbds['dlon'] <= obloc['lon'] < boxbds['clon']+boxbds['dlon']:
            yesinbox = True
    return(yesinbox)

def findclosest(target, stationlist, target_imputations, row, sdata):
    """
    Find a suitable donor station for the target and year.

    Parameters:
    target : str : Target station ID.
    stationlist : dict : Metadata for all available stations.
    target_imputations : dict : Number of previous imputations
        for each target station.
    row : pd.Series : Station values for the year being imputed.
    sdata : pd.DataFrame : Original station observations used
        for donor similarity calculations.

    Returns:
    str : Selected donor station ID, or 'Nogood' if none is found.
    """

    # ---------- RMSD AND BOUNDED PC1 DISTANCE ----------
    # Search radii: 100 km, 150 km, ... until a usable donor is found.
    if method in (1, 3):
        base_radius = 100.0
        max_radius = 5000.0
        step = 50.0

        # Candidates must have a value for this year
        candidates_with_value = [
            cand for cand in stationlist.keys()
            if cand != target and pd.notna(row[cand])
        ]
        if not candidates_with_value:
            return 'Nogood'

        radius = base_radius
        while radius <= max_radius:
            bestcand = 'Nogood'
            best_dist = float('inf')

            # Only consider stations within this radius
            nearby = [
                cand for cand in candidates_with_value
                if greatcircdist(stationlist, target, cand) < radius
            ]
            print(f"{target} year={row.name}: radius={radius} km, nearby={len(nearby)}")

            for candidate in nearby:
                if method == 1:
                    d = rmsd_distance(stationlist, sdata, target, candidate, radius)
                elif method == 3:
                    d = pc1_distance(stationlist, target, candidate, radius) 
                if np.isfinite(d) and d < best_dist:
                    best_dist = d
                    bestcand = candidate

            if bestcand != 'Nogood':
                return bestcand

            radius += step  
            
        return 'Nogood'

    # ---------- ANTIDISTANCE AND PC SCORES ----------
    # Initialize square of distance to very large number of degrees latitude squared
    dist2 = 10000.0
    bestcand = 'Nogood'

    for candidate in stationlist.keys():
        if candidate != target and ~np.isnan(row[candidate]):
            weight = target_imputations[target]

            if method == 0:
                candist2 = antidistance2(stationlist, target, candidate, weight)
            elif method == 2:
                candist2 = pc_score_distance(stationlist, target, candidate)
            else:
                continue

            if candist2 < dist2:
                dist2 = candist2
                bestcand = candidate

    return bestcand


def choose_target_stations(obmeta, sentinel_stations, impute_targets):
    """
    Decide which stations to impute.

    Parameters:
    obmeta : dict : Metadata for all loaded stations.
    sentinel_stations : set : Sentinel station IDs.
    impute_targets : int : 0 = all stations, 1 = sentinel only.

    Returns:
    list : Station IDs selected for imputation.
    """
    all_stations = list(obmeta.keys())

    if impute_targets == 0:
        # Impute for everything we've loaded into sdata
        return all_stations

    if impute_targets == 1:
        # Impute only sentinel stations that are actually present in sdata
        return [stn for stn in all_stations if stn in sentinel_stations]

# %% 12. SETS UP DFs FOR IMPUTATION
# ==========================================================

sentinel_df = pd.read_csv(sentinel_csv)
sentinel_stations = set(sentinel_df['stn'].astype(str) + '_1d')

def load_or_build_sdata(ival: str):
    """
    Return (sdata, obmeta) for a given interval.
    If reuse_sdata is True and file exists, load it; otherwise build from raw.
    """
    sdata_file = get_sdata_filename(ival)

    # Try to reuse if allowed and file exists
    if reuse_sdata and os.path.exists(sdata_file):
        print(f"Loading previously saved sdata: {sdata_file}")
        sdata = pd.read_csv(sdata_file, index_col=0, low_memory=False)
        sdata.index = [int(x) if str(x).isdigit() else x for x in sdata.index]

        if 'Latitude' not in sdata.index or 'Longitude' not in sdata.index:
            raise ValueError("Saved sdata file is missing Latitude/Longitude rows!")

        obmeta = {}
        lat_row = sdata.loc['Latitude']
        lon_row = sdata.loc['Longitude']
        for stn in sdata.columns:
            if pd.notna(lat_row.get(stn)) and pd.notna(lon_row.get(stn)):
                obmeta[stn] = {
                    'stid': stn,
                    'lat': float(lat_row[stn]),
                    'lon': float(lon_row[stn]),
                    'wlat': float(lat_row[stn]),
                    'wlon': float(lon_row[stn]),
                }
        sdata = sdata.drop(index=['Latitude', 'Longitude'])
        sdata = sdata.apply(pd.to_numeric, errors='raise')
        
        return sdata, obmeta

    # Otherwise: build from raw GHCN-D files
    print(f"Building sdata from raw files for interval {ival} (network={networks[network]})")
    obs = GHCN(os.path.join(datadir, dataext))
    total_files = len(obs.files)
    firstob = True
    obmeta = {}
    file_counter = 0

    for ob in obs:
        if inbox(ob[0], boxbds):
            obmeta[ob[0]['stid']] = ob[0]
            if firstob:
                sdata = dfob(ob)
                firstob = False
            else:
                sdata = dfob(ob, addto=sdata)
        file_counter += 1
        if file_counter % 100 == 0 or file_counter == total_files:
            print(f"Read {file_counter}/{total_files} files")

    sdata = sdata[(sdata.index >= syear) & (sdata.index <= eyear)].sort_index()

    # Add meta rows for later reuse
    sdata_with_meta = sdata.copy()
    sdata_with_meta.loc['Latitude'] = pd.Series({stn: obmeta[stn]['lat'] for stn in sdata.columns})
    sdata_with_meta.loc['Longitude'] = pd.Series({stn: obmeta[stn]['lon'] for stn in sdata.columns})
    sdata_with_meta.to_csv(sdata_file)
    print(f"Saved sdata to {sdata_file}")

    return sdata, obmeta

    
for ival in interval:
    sdata, obmeta = load_or_build_sdata(ival)
       
    # Build fdata with years + meta rows in one shot
    fdata = pd.DataFrame(
        index=list(sdata.index) + ['Latitude', 'Longitude'],
        columns=sdata.columns,
        data=np.nan,
    ) 
    
    # Track how often each donor is used for each target
    imputations = defaultdict(lambda: defaultdict(int))

    # Track total successful imputations for each target
    target_imputations = defaultdict(int)
    
    # Create dictionary entries for tracking locations of used neighboring stations
    for stn, meta in obmeta.items():
        meta['wlat'] = meta['lat']
        meta['wlon'] = meta['lon']
        fdata.at['Latitude', stn] = meta['lat']
        fdata.at['Longitude', stn] = meta['lon']

# %% 13. HOTDECK IMPUTATION
# ==========================================================
       
    stations_to_process = choose_target_stations(
        obmeta=obmeta,
        sentinel_stations=sentinel_stations,
        impute_targets=impute_targets,
    )
    total = len(stations_to_process)
    complete = 0
    
    for targetstn in stations_to_process:
        print(ival, targetstn)
        
        # Create a tracker dataframe for each target station
        if track == 1:
            trackerdf = create_station_df([])
            
        for index, row in sdata.iterrows():
            if syear <= index <= eyear:
                if np.isnan(row[targetstn]):  # Missing observation
                
                    goodneighbor = findclosest(targetstn, obmeta, target_imputations, row, sdata)
                    
                    if goodneighbor == 'Nogood':  # No imputable station found
                        fdata.at[index, targetstn] = np.nan
                        if track == 1:
                            trackerdf = update_station_df(
                                index, np.nan, 'Nogood', np.nan, np.nan, np.nan, trackerdf
                            )
                            
                    else:
                        donor_val = sdata.at[index, goodneighbor]
                        
                        # Impute the missing value
                        fdata.at[index, targetstn] = donor_val
                        
                        # Number of donors already used for this target
                        count = target_imputations[targetstn]
                        
                        # Add imputation to the tracker dataframe
                        if track == 1:
                            trackerdf = update_station_df(
                                index, donor_val, goodneighbor,
                                obmeta[goodneighbor]['lat'],
                                obmeta[goodneighbor]['lon'],
                                greatcircdist(obmeta, targetstn, goodneighbor),
                                trackerdf
                            )
    
                        # Update the average location of previously used donors
                        # when using ANTIDISTANCE
                        if method == 0:
                            update_imputed_location(
                                obmeta, targetstn, goodneighbor, count
                            )
                        
                        # Keep candidate-specific count for tracking donor usage
                        imputations[goodneighbor][targetstn] += 1

                        # Increment total imputations received by this target
                        target_imputations[targetstn] += 1
    
                else:
                    # Preserve original observed values
                    fdata.at[index, targetstn] = sdata.at[index, targetstn]

                    if track == 1:
                        trackerdf = update_station_df(
                            index, sdata.at[index, targetstn],
                            np.nan, np.nan, np.nan, np.nan, trackerdf
                        )
                        
        # Save station's tracker dataframe to a CSV file
        if track == 1:
            write_tracker_file(targetstn, trackerdf, station_csv_dir)
            
        # Increment completed stations counter and print progress
        complete += 1
        print(f"Progress: {complete}/{total}")
        
    # Save imputed dataframe
    fdata = fdata[stations_to_process]
    fdata.to_csv(framedir + ival + framext)
    
# %% 14. CALCULATE SCRIPT RUN TIME
# ==========================================================
end_time = time.time()
execution_time = end_time - start_time
if execution_time <= 60:
    print(f"Execution time: {execution_time:.2f} seconds")
elif execution_time <= 3600:
    execution_time = execution_time/60
    print(f'Execution time: {execution_time:.2f} minutes')
else:
    execution_time = execution_time/3600
    print(f'Execution time: {execution_time:.2f} hours')