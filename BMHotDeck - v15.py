# In[]:=====================================================
# 1. CONFIGURATION
# ==========================================================

# Reuse a saved sdata file?
    # 0 = No, regenerate from raw GHCN-D files
    # 1 = Yes, use saved CSV
reuse_sdata = 1

# Is the data modified for testing?
    # 0 = No, includes all obs
    # 1 = missing some obs across years
test = 0
num_test = 1

# Range of years
syear = 1895
eyear = 2024

# Choose station network for donor pool
    # 0 = full
    # 1 = 30-year minimum
    # 2 = sentinel
network = 1

# Choose which stations to IMPUTE for (targets)
    # 0 = all stations in sdata
    # 1 = sentinel stations only
impute_targets = 1

# Set the lat/lon bounds
boxbds = {'clat':37.2, #center lat
          'clon':-95.7, #center lon
          'dlat': 12.7, #lat range
          'dlon': 29.6, #lon range
          } 

# Frequency Interval
interval = ['01d']
interval_str = interval[0]

# Method for "Find Closest"
    # 0 - Antidistance
    # 1 - Unbounded Euclidean
    # 2 - Bounded Euclidean
    # 3 - PC scores
    # 4 - Flexible Bounded Euclidean
    # 5 - PC Antidistance
    # 6 - Flexible Bounded PC1
method = 1

# PCA variance explained (for PC weighting)
PC1 = 0.618822012410706
PC2 = 0.118309243866165
PC3 = 0.0972184973164955

# Use adjustment factor?
    # 0 - No
    # 1 - Yes
adjustment_factor = 0

# Tracker files?
    # 0 - No
    # 1 - Yes
track = 0

# Map results?
    # 0 - No
    # 1 - Yes
mapping = 1

# In[]:=====================================================
# 2. MAPPING TITLES
# ==========================================================

# For titles
adjusted_label = ' (Adj.)' if adjustment_factor == 1 else ''
testing_label = f' (Test {num_test})' if test == 1 else ''

# Tags for pool (sdata) vs targets (imputed stations)
pool_names = {
    0: "Full Network",
    1: "30-Year Minimum",
    2: "Sentinel Only",
}
target_names = {
    0: "All Stations",
    1: "Sentinel Stations Only",
}

# These stay readable for the map titles
pool_label = pool_names[network]
target_label = target_names[impute_targets]

method_titles = {
    0: f'{interval_str} Mean ABM ({syear}-{eyear}) - Antidistance{adjusted_label}{testing_label}\n'
       f'Donor Pool: {pool_label} | Imputed: {target_label}',
    1: f'{interval_str} Mean ABM ({syear}-{eyear}) - Euclidean{adjusted_label}{testing_label}\n'
       f'Donor Pool: {pool_label} | Imputed: {target_label}',
    2: f'{interval_str} Mean ABM ({syear}-{eyear}) - Bounded Euclidean{adjusted_label}{testing_label}\n'
       f'Donor Pool: {pool_label} | Imputed: {target_label}',
    3: f'{interval_str} Mean ABM ({syear}-{eyear}) - PC Scores{adjusted_label}{testing_label}\n'
       f'Donor Pool: {pool_label} | Imputed: {target_label}',
    4: f'{interval_str} Mean ABM ({syear}-{eyear}) - Flex Bounded Euclidean{adjusted_label}{testing_label}\n'
       f'Donor Pool: {pool_label} | Imputed: {target_label}',
    5: f'{interval_str} Mean ABM ({syear}-{eyear}) - PC Antidistance{adjusted_label}{testing_label}\n'
       f'Donor Pool: {pool_label} | Imputed: {target_label}',
    6: f'{interval_str} Mean ABM ({syear}-{eyear}) - Flex Bounded PC1{adjusted_label}{testing_label}\n'
       f'Donor Pool: {pool_label} | Imputed: {target_label}',
}
title = method_titles.get(method)

# In[]:=====================================================
# 3. DIRECTORIES/FILE PATHS
# ==========================================================
datadir = '/HotDeck/N-G-Hot-Deck/N-G-Hot-Deck/raw/'
networks = {
    0: 'GHCN-D',
    1: 'GHCN-D_30yrs',
    2: 'GHCN-D_sentinel'
}
dataext = networks.get(network)

# For filenames (no spaces)
adjusted_tag = 'adjusted' if adjustment_factor == 1 else 'unadjusted'
testing_tag = f'test{num_test}' if test == 1 else ''
pool_tags = {
    0: "poolFull",
    1: "pool30yr",
    2: "poolSentinel",
}
target_tags = {
    0: "targetsAll",
    1: "targetsSentinel",
}
pool_tag = pool_tags[network]
target_tag = target_tags[impute_targets]

framedir = '/HotDeck/N-G-Hot-Deck/N-G-Hot-Deck/frame/'
output_names = {
    0: f'_bigbox_filled_{adjusted_tag}ad_{pool_tag}_{target_tag}{testing_tag}.csv',
    1: f'_bigbox_filled_{adjusted_tag}euc_{pool_tag}_{target_tag}{testing_tag}.csv',
    2: f'_bigbox_filled_{adjusted_tag}beuc_{pool_tag}_{target_tag}{testing_tag}.csv',
    3: f'_bigbox_filled_{adjusted_tag}pc_{pool_tag}_{target_tag}{testing_tag}.csv',
    4: f'_bigbox_filled_{adjusted_tag}feuc_{pool_tag}_{target_tag}{testing_tag}.csv',
    5: f'_bigbox_filled_{adjusted_tag}pcad_{pool_tag}_{target_tag}{testing_tag}.csv',
    6: f'_bigbox_filled_{adjusted_tag}flexpc1_{pool_tag}_{target_tag}{testing_tag}.csv',
}
framext = output_names.get(method)
tracker_base = framext.replace('_bigbox_filled_', '').replace('.csv', '')
sentinel_csv = '/HotDeck/N-G-Hot-Deck/N-G-Hot-Deck/sentinelstations.csv'
station_csv_dir = '/HotDeck/N-G-Hot-Deck/N-G-Hot-Deck/trackerfiles/'
map_shps = '/HotDeck/N-G-Hot-Deck/N-G-Hot-Deck/map_shps'
pc_files = {
    0: f'/HotDeck/N-G-Hot-Deck/N-G-Hot-Deck/pca_scores_{networks[network]}.csv',
    1: f'/HotDeck/N-G-Hot-Deck/N-G-Hot-Deck/pca_scores_{networks[network]}_modified{num_test}.csv'
}
pc_score_file = pc_files.get(test)
prcptot_dir = '/HotDeck/N-G-Hot-Deck/N-G-Hot-Deck/PRCPTOT'

def get_sdata_filename(ival: str) -> str:
    """
    Build a unique sdata filename based on key config options so that
    reuse_sdata=1 never accidentally pulls a mismatched file.
    """
    net_tag = networks[network]
    bbox_tag = (f"_{boxbds['clat']:.1f}N_{boxbds['clon']:.1f}E_"
                f"d{boxbds['dlat']:.1f}x{boxbds['dlon']:.1f}")
    year_tag = f"_{syear}-{eyear}"
    
    if test == 1:
        return f"{ival}_{net_tag}{year_tag}{bbox_tag}_modified{num_test}_sdata.csv"
    else:
        return f"{ival}_{net_tag}{year_tag}{bbox_tag}_sdata.csv"

# In[]:=====================================================
# 4. IMPORTS
# ==========================================================

import os
import csv
import warnings
import pandas as pd
import numpy as np
from geopy.distance import great_circle 
from collections import defaultdict 
import time

start_time = time.time()

# Suppress future warnings
warnings.simplefilter(action = "ignore", category = FutureWarning)

# In[]:=====================================================
# 5. READING IN THE BLOCK MAXIMA DATA
# ==========================================================
class GHCN(object):
    """
    Iterator over GHCN-like CSV files in a directory.

    Each CSV is assumed to have:
    col[0] = date (mm/dd/YYYY)
    col[1] = precip value
    col[5] = station name
    col[6] = lat
    col[7] = lon
    col[8] = elevation (optional)
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

# In[]:=====================================================
# 6. TRACKER FILES FUNCTIONS
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
    
    trackerdf = pd.concat([trackerdf, new_row], ignore_index=True)
    return trackerdf  # Return the updated dataframe

def write_tracker_file(station_id, trackerdf, directory):
    """
    Save the station tracker dataframe to a CSV file.
    
    Parameters:
    station_id : str : The station ID.
    trackerdf : pd.DataFrame : The dataframe to be saved.
    directory : str : The directory to save the CSV.
    """
    tracker_fname = f"{tracker_base}__{targetstn}.tracker.csv"
    trackerdf.to_csv(
        os.path.join(station_csv_dir, tracker_fname),
        index=False
    )

# In[]:=====================================================
# 7. CREATE SDATA
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

# In[]:=====================================================
# 8. GREAT CIRCLE DISTANCE CALCULATION
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

# In[]:=====================================================
# 9. GEOGRAPHICAL ANTIDISTANCE FUNCTION
# ==========================================================

def antidistance2(stationlist, target, candidate, weight):
    """
    Compute the distance between the desired station location and the candidate's location.
    
    Parameters:
    stationlist : dict : List of stations with their metadata.
    target : str : The target station ID.
    candidate : str : The candidate station ID.
    weight : int : The number of imputations done so far.
    
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
    
# In[]:=====================================================
# 10. EUCLIDEAN DISTANCE FUNCTIONS
# ==========================================================

if method in (1, 2, 4):
    euc_cache = defaultdict(dict)

def euclidean_distance(stationlist, sdata, target, candidate):
    """
    Calculate the Euclidean distance between target and candidate stations.
    
    Parameters:
    stationlist : dict : List of stations with their metadata.
    sdata : pd.DataFrame : DataFrame containing station precip data.
    target : str : The target station ID.
    candidate : str : The candidate station ID.
    
    Returns:
    float : The Euclidean distance.
    """
    if track == 1:
        greatcircdist(stationlist,target,candidate)
    
    # Check if the value is cached as "Nogood" or already calculated and handle as necessary
    if candidate in euc_cache[target]:
        cached_value = euc_cache[target][candidate]
        if cached_value == 'Nogood':
            return float('inf')
        return cached_value
    
    # Identify target/candidate precip values
    target_precip = sdata[target]
    # print(target_precip)
    candidate_precip = sdata[candidate]

    # Find common years where both stations have data
    common_years = target_precip.dropna().index.intersection(candidate_precip.dropna().index)
    if common_years.empty:
        # No common data, mark as 'Nogood' and return a large distance value
        euc_cache[target][candidate] = 'Nogood'
        euc_cache[candidate][target] = 'Nogood'
        return float('inf')

    # Cut down precipitation data to common years
    target_precip = target_precip.loc[common_years].values
    candidate_precip = candidate_precip.loc[common_years].values

    # Calculating the Euclidean distance and caching it
    euc = np.sqrt(np.mean((target_precip - candidate_precip) ** 2))
    euc_cache[target][candidate] = euc
    euc_cache[candidate][target] = euc

    return euc

def bounded_euclidean_distance(stationlist, sdata, target, candidate):
    """
    Calculate the bounded Euclidean distance between target and candidate stations.
    
    Parameters:
    stationlist : dict : List of stations with their metadata.
    sdata : pd.DataFrame : DataFrame containing station precip data.
    target : str : The target station ID.
    candidate : str : The candidate station ID.
    
    Returns:
    float : The bounded Euclidean distance.
    """

    # Check if the value is cached as "Nogood" or already calculated and handle as necessary
    if candidate in euc_cache[target]:
        cached_value = euc_cache[target][candidate]
        if cached_value == 'Nogood':
            return float('inf')
        return cached_value
    
    # Calculate the great-circle distance and check if stn is inbounds    
    distance = greatcircdist(stationlist,target,candidate)
        
    if distance >= 100:
        euc_cache[target][candidate] = 'Nogood'
        euc_cache[candidate][target] = 'Nogood'
        return float('inf')
    
    # Identify target/candidate precip values
    target_precip = sdata[target]
    candidate_precip = sdata[candidate]

    # Find common years where both stations have data
    common_years = target_precip.dropna().index.intersection(candidate_precip.dropna().index)
    if common_years.empty:
        # No common data, mark as 'Nogood' and return a large distance value
        euc_cache[target][candidate] = 'Nogood'
        euc_cache[candidate][target] = 'Nogood'
        return float('inf')

    # Cut down precipitation data to common years
    target_precip = target_precip.loc[common_years].values
    candidate_precip = candidate_precip.loc[common_years].values

    # Calculating the Euclidean distance and caching it
    euc = np.sqrt(np.mean((target_precip - candidate_precip) ** 2))
    euc_cache[target][candidate] = euc
    euc_cache[candidate][target] = euc 

    return euc

def flexible_bounded_euclidean_distance(stationlist, sdata, target, candidate, radius):
    """
    Flexible bounded Euclidean distance:
    - Uses radius (km) as an upper bound
    - Caches only:
        * finite Euclidean distances (over common years)
        * 'Nogood' ONLY when there are no common years
    - IMPORTANT: radius is ALWAYS enforced, even when Euclidean is cached
    """

    # Always enforce radius first (great-circle is cached in dist_cache)
    distance_km = greatcircdist(stationlist, target, candidate)
    if distance_km >= radius:
        return float('inf')

    # If Euclidean is cached, return it (radius already enforced above)
    if candidate in euc_cache[target]:
        cached_value = euc_cache[target][candidate]
        if cached_value == 'Nogood':  # means no common years
            return float('inf')
        return cached_value

    # Otherwise compute Euclidean using common years
    target_precip = sdata[target]
    candidate_precip = sdata[candidate]

    common_years = target_precip.dropna().index.intersection(candidate_precip.dropna().index)
    if common_years.empty:
        # No common data -> truly invalid for all radii
        euc_cache[target][candidate] = 'Nogood'
        euc_cache[candidate][target] = 'Nogood'
        return float('inf')

    # Cut down precipitation data to common years
    target_precip = target_precip.loc[common_years].values
    candidate_precip = candidate_precip.loc[common_years].values

    # Calculating the Euclidean distance and caching it
    euc = np.sqrt(np.mean((target_precip - candidate_precip) ** 2))
    euc_cache[target][candidate] = euc
    euc_cache[candidate][target] = euc   

    return euc


# In[]:=====================================================
# 11. PC SCORES FUNCTIONS
# ==========================================================

# Read PCA Scores into Dictionary
if method in (3,5,6):
    pc_df = pd.read_csv(pc_score_file)
    pc_scores = {}
    for _, row in pc_df.iterrows():
        station_id = str(row['Station']).strip()
        # Remove '_1d' if present, to ensure consistency
        if station_id.endswith('_1d'):
            station_id = station_id[:-3]
        pc_scores[station_id] = [row['PC1'], row['PC2'], row['PC3']]
    pc_cache = defaultdict(dict)
    if method == 6:
        pc1_cache = defaultdict(dict)

def pc_score_distance(stationlist, target, candidate):
    """
    Compute the weighted distance between two stations in PC1–PC3 space,
    giving more weight to the PCs that explain more variance.
    """
    if track == 1:
        greatcircdist(stationlist,target,candidate)
    target = target.split('_')[0]
    candidate = candidate.split('_')[0]
    
    if candidate in pc_cache[target]:
        return pc_cache[target][candidate]
    
    target_vec = np.array(pc_scores[target])
    candidate_vec = np.array(pc_scores[candidate])
    
    # Explained variance weights (normalized or not)
    pc_var = np.array([PC1, PC2, PC3])  # Replace with your actual PCA values
    pc_weights = pc_var
    
    # Weighted Euclidean distance
    diff = target_vec - candidate_vec
    weighted_pc_dist = np.sqrt(np.sum(pc_weights * diff**2))
       
    # Store in cache both directions
    pc_cache[target][candidate] = weighted_pc_dist
    pc_cache[candidate][target] = weighted_pc_dist
    
    return weighted_pc_dist

def pc_antidistance(stationlist, target, candidate, weight):
    """
    Antidistance logic in PC space (PC1–PC3), using a weighted mean vector.
    
    Parameters:
    target : str : The target station ID
    candidate : str : The candidate station ID
    weight : int : Number of imputations done so far
    
    Returns:
    float : Squared distance in PC space from weighted target to candidate
    """
    if track == 1:
        greatcircdist(stationlist,target,candidate)
        
    # define new variables for the PCA lookup only:
    target_id = target.split('_')[0]
    candidate_id = candidate.split('_')[0]
    
    candidate_vec = np.array(pc_scores[candidate_id])
    target_vec = np.array(pc_scores[target_id])
    wvec = np.array([
        obmeta[target]['wPC1'],
        obmeta[target]['wPC2'],
        obmeta[target]['wPC3']
    ])
    
    anti_vec = (weight+1)*target_vec - weight*wvec
    
    # Use explained variance as weights
    pc_var = np.array([PC1, PC2, PC3])
    pc_weights = pc_var
    
    # Apply weighted squared distance
    diff = candidate_vec - anti_vec
    dvec = np.sqrt(np.sum(pc_weights * diff**2))
    
    return dvec

def update_imputed_pc_location(obmeta, targetstn, goodneighbor, count):
    """
    Update the mean PC location of all donors previously
    used to impute the target.

    count = number of previous imputations for this target
    """
    for i, key in enumerate(['wPC1', 'wPC2', 'wPC3']):
        oldval = obmeta[targetstn][key]
        newval = pc_scores[goodneighbor.split('_')[0]][i]

        obmeta[targetstn][key] = (
            oldval * count + newval
        ) / (count + 1)
        
def pc1_distance(stationlist, target, candidate, radius):
    
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

# In[]:=====================================================
# 12. FINDING SUITABLE DONOR
# ==========================================================

def inbox(obloc,boxbds):
    yesinbox = False
    if boxbds['clat']-boxbds['dlat'] <= obloc['lat'] < boxbds['clat']+boxbds['dlat']:
        if boxbds['clon']-boxbds['dlon'] <= obloc['lon'] < boxbds['clon']+boxbds['dlon']:
            yesinbox = True
    return(yesinbox)    

def findclosest(target, stationlist, imputations, target_imputations, row, sdata):
    """
    Find the best station to use for imputation based on parameter of choice and weight.

    Parameters:
    obmeta : dict : Metadata for all stations.
    target : str : The target station ID.
    sdata : pd.DataFrame : DataFrame containing station data.
    targetimputations : pd.DataFrame : DataFrame tracking imputations.
    weight : int : The weight factor representing number of imputations.

    Returns:
    str : The ID of the closest station.
    """

    # ---------- FLEXIBLE BOUND ----------
    # This branch searches by radius first: 100 km, 150 km, ... until a usable donor is found.
    if method in (4,6):
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
                if method == 4:
                    d = flexible_bounded_euclidean_distance(stationlist, sdata, target, candidate, radius)
                elif method == 6:
                    d = pc1_distance(stationlist, target, candidate, radius) 
                if np.isfinite(d) and d < best_dist:
                    best_dist = d
                    bestcand = candidate

            if bestcand != 'Nogood':
                return bestcand  # stop immediately once a donor exists in this radius

            radius += step
            
        print(f"{target} year={row.name}: FOUND {bestcand} at radius={radius} km, gc={greatcircdist(stationlist,target,bestcand):.1f} km, dist={best_dist:.3f}")
        return 'Nogood'

    # ---------- ALL OTHER METHODS (0–3) ----------
    # Initialize square of distance to very large number of degrees latitude squared
    dist2 = 10000.0
    bestcand = 'Nogood'

    # Check all candidate stations (slow but effective)
    for candidate in stationlist.keys():
        # First tests: not the same station, and has valid data
        if candidate != target and ~np.isnan(row[candidate]):
            weight = target_imputations[target]

            if method == 0:
                candist2 = antidistance2(stationlist, target, candidate, weight)
            elif method == 1:
                candist2 = euclidean_distance(stationlist, sdata, target, candidate)
            elif method == 2:
                candist2 = bounded_euclidean_distance(stationlist, sdata, target, candidate)
            elif method == 3:
                candist2 = pc_score_distance(stationlist, target, candidate)
            elif method == 5:
                candist2 = pc_antidistance(stationlist, target, candidate, weight)
            else:
                # Unknown method for this branch; skip
                continue

            if candist2 < dist2:
                dist2 = candist2
                bestcand = candidate

    return bestcand


def choose_target_stations(obmeta, sentinel_stations, impute_targets):
    """
    Decide which stations we actually impute for.

    Parameters
    ----------
    obmeta : dict
        Metadata dict for all stations in sdata (keys = station IDs).
    sentinel_stations : set
        Set of sentinel station IDs like 'USC00010008_1d'.
    impute_targets : int
        0 = all stations in sdata
        1 = sentinel stations only

    Returns
    -------
    list of station IDs to iterate as targets.
    """
    all_stations = list(obmeta.keys())

    if impute_targets == 0:
        # Impute for everything we've loaded into sdata
        return all_stations

    if impute_targets == 1:
        # Impute only sentinel stations that are actually present in sdata
        return [stn for stn in all_stations if stn in sentinel_stations]

    # Fallback (shouldn't really hit)
    return all_stations

# In[]:=====================================================
# 13. ADJUSTING DONOR TOTAL
# ==========================================================

if adjustment_factor == 1:
    prcptot_means = {}
    
    for fname in os.listdir(prcptot_dir):
        if fname.endswith('_PRCPTOT.csv'):
            stnid = fname.split('_')[0]  # Extract station ID prefix
            df = pd.read_csv(os.path.join(prcptot_dir, fname))
            
            # Filter to imputation years only
            df = df[(df['year'] >= syear) & (df['year'] <= eyear)]
            
            # Convert "NA" to NaN and compute mean
            df['prcptot'] = pd.to_numeric(df['prcptot'], errors='coerce')
            prcptot_means[stnid] = df['prcptot'].mean(skipna=True)

# In[]:=====================================================
# 14. SETS UP DFs FOR IMPUTATION
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
        sdata = pd.read_csv(sdata_file, index_col=0)
        sdata.index = [int(x) if str(x).isdigit() else x for x in sdata.index]

        if 'Latitude' not in sdata.index or 'Longitude' not in sdata.index:
            raise ValueError("Saved sdata file is missing Latitude/Longitude rows!")

        obmeta = {}
        lat_row = sdata.loc['Latitude']
        lon_row = sdata.loc['Longitude']
        for stn in sdata.columns:
            if pd.notna(lat_row.get(stn)) and pd.notna(lon_row.get(stn)):
                if method == 5:
                    stnid = stn.split('_')[0]
                    if stnid in pc_scores:
                        obmeta[stn] = {
                            'stid': stn,
                            'lat': float(lat_row[stn]),
                            'lon': float(lon_row[stn]),
                            'wlat': float(lat_row[stn]),
                            'wlon': float(lon_row[stn]),
                            'wPC1': float(pc_scores[stnid][0]),
                            'wPC2': float(pc_scores[stnid][1]),
                            'wPC3': float(pc_scores[stnid][2]),
                        }
                else:
                    obmeta[stn] = {
                        'stid': stn,
                        'lat': float(lat_row[stn]),
                        'lon': float(lon_row[stn]),
                        'wlat': float(lat_row[stn]),
                        'wlon': float(lon_row[stn]),
                    }
        sdata = sdata.drop(index=['Latitude', 'Longitude'])
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

    # Imputation Count initialized
    imputations = defaultdict(lambda: defaultdict(int))
    # Total number of imputations received by each target
    target_imputations = defaultdict(int)
    
    # Create dictionary entries for tracking locations of used neighboring stations
    for stn, meta in obmeta.items():
        meta['wlat'] = meta['lat']
        meta['wlon'] = meta['lon']
        fdata.at['Latitude', stn] = meta['lat']
        fdata.at['Longitude', stn] = meta['lon']

# In[]:=====================================================
# 15. HOTDECK IMPUTATION
# ==========================================================
       
    stations_to_process = choose_target_stations(
        obmeta=obmeta,
        sentinel_stations=sentinel_stations,
        impute_targets=impute_targets,
    )
    total = len(stations_to_process)
    complete = 0    
    
    for targetstn in stations_to_process: # Outer loop now iterates by station
        print(ival, targetstn)
        
        # Create a tracker dataframe for each target station
        if track == 1:
            trackerdf = create_station_df([])
            
        for index, row in sdata.iterrows():  # Inner loop iterates by year
            if syear <= index <= eyear:
                if np.isnan(row[targetstn]):  # Data's missing; we need to impute
                
                    goodneighbor = findclosest(targetstn, obmeta, imputations, target_imputations, row, sdata)
                    
                    if goodneighbor == 'Nogood':  # No imputable station found
                        fdata[targetstn][index] = np.nan
                        if track == 1: 
                            update_station_df(index, np.nan, 'Nogood', np.nan, np.nan, np.nan, trackerdf)
                            
                    else:
                        
                        donor_val = sdata[goodneighbor][index]
                        
                        if adjustment_factor == 1:
                            # Adjustment Factor
                            rec_id = targetstn.split('_')[0]
                            don_id = goodneighbor.split('_')[0]
                            if rec_id in prcptot_means and don_id in prcptot_means:
                                donor_mean = prcptot_means[don_id]
                                rec_mean = prcptot_means[rec_id]
                                if donor_mean and not np.isnan(donor_mean):
                                    factor = rec_mean / donor_mean
                                    donor_val = donor_val * factor
                        
                        # Impute and adjust imputation count
                        fdata[targetstn][index] = donor_val
                        # Number of donors that have ALREADY been used for this target
                        count = target_imputations[targetstn]
                        
                        # Adding imputation to the tracker dataframe
                        if track == 1:
                            trackerdf = update_station_df(
                                index, fdata[targetstn][index], goodneighbor, 
                                obmeta[goodneighbor]['lat'], obmeta[goodneighbor]['lon'], 
                                dist_cache[targetstn][goodneighbor], trackerdf
                            )
    
                        # Update the average of all imputed station locations if using ANTIDISTANCE
                        if method == 0:
                            update_imputed_location(obmeta, targetstn, goodneighbor, count)
                        if method == 5:
                            update_imputed_pc_location(obmeta, targetstn, goodneighbor, count)
                            
                        
                        # Keep candidate-specific count for tracking donor usage
                        imputations[goodneighbor][targetstn] += 1

                        # Increment total imputations received by this target
                        target_imputations[targetstn] += 1
    
                else:
                    fdata[targetstn][index] = sdata[targetstn][index]
                    if track == 1:
                        trackerdf = update_station_df(index, sdata[targetstn][index], np.nan, np.nan, np.nan, np.nan, trackerdf)
        # Save station's tracker dataframe to a CSV file
        if track == 1:
            write_tracker_file(targetstn, trackerdf, station_csv_dir)
            
        # Increment completed stations counter and print progress
        complete += 1
        print(f"Progress: {complete}/{total}")
    # Saving imputed dataframe 
    fdata = fdata[stations_to_process]
    fdata.to_csv(framedir + ival + framext)

# In[]: CALCULATE SCRIPT RUN TIME
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