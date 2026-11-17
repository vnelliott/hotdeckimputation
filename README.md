# Hot Deck Imputation of Annual Block Maximum Precipitation

## Overview
This repository contains Python code for imputing missing annual block maximum (ABM) precipitation values using hot deck imputation. 
The program identifies suitable donor stations with available observations and uses their corresponding values to fill missing observations at target stations.

Four donor-selection methods are implemented:

1. **Antidistance:** Based on geographic proximity
2. **Root Mean Square Difference (RMSD):** Based on similar ABM time series
3. **PC Scores:** Based on similarity in principal component (PC) space after combining geographical and climatological variables using principal component analysis (PCA)
4. **Bounded PC1 Distance:** Based on PC 1 score similarity

The program is pretty versatile and supports using different station networks, geographic domains, and study periods. 
Users can select the donor-selection method, specify which stations from the network will be imputed, and optionally generate tracking files identifying the donors used for each imputation. 
Should one desire, it is easy to add new donor-selection methods beyond what is currently in the script.

## Repository Structure
### frame
Once imputation is complete, the resulting filled ABM dataset is saved here as a .csv file. 

An example file, 01d_bigbox_filled_ad_poolSentinel_targets_Sentinel.csv, is included here. 
01d indicates the file has 1-day ABM values, ad indicates antidistance was used as the donor-selection method, poolSentinel means the donor pool used was the sentinel network, and targetsSentinel means imputation was done 
on the sentinel network. Columns are each station and rows are each year (with the last two rows including the latitude and longitude values of the stations).

### raw
This is where the original, unfilled ABM .csv files go. You must declare which folder of data within the raw folder gets used in the imputation script.

For our project, we had three folders within the raw folder named GHCN-D (all stations), GHCN-D_30yrs (stations with at least 30 years of good data), 
and GHCN-D_sentinel (stations with at least 90 years of good data). Here, I only show one of these folders with example files. Each file is labeled as its stationid_1d.csv (1d for 1-day ABM), and within the files, 
columns include DT (date, but the year is the key bit of info here), max (the maximum 1-day value for the year), idmax (the day the maximum was recorded), fm (the fraction of missing data for this calendar year), 
NETWORK (which dataset the precip data comes from), NAME (full name of the station), LAT (latitude), LON (longitude), and ELEV (elevation). Each row corresponds to each year of data.

### trackerfiles
For each station, a tracker file is made to track the donors used to impute their incomplete series and they are stored in this folder as .csv files. You must indicate if you want tracker files to be written within 
the script.

An example file, ad_poolSentinel_targetsSentinel_USC00122605_1d.tracker.csv, is included here. ad indicates antidistance was used as the donor-selection method, poolSentinel means the donor pool used was the sentinel 
network, targetsSentinel means imputation was done  on the sentinel network, USC00122605 is the station ID this file is for, and 1d indicates the file has 1-day ABM values. Within the files, the columns include Year, Value
(the observed or imputed ABM value for that year), Donor (formatted as stationid_1d), Donor Lat, Donor Lon, and Distance (the distance in kilometers of the donor to the receiving station). Each row corresponds to each year within the study period.
For years where Donor, Donor Lat, Donor Lon, and Distance are blank, there was an observation available in the original time series and no donor was needed. The value listed then is the original value in the data.

### 01d_GHCN-D_sentinel_1895-2024_37.2N_-95.7E_d12.7x29.6_sdata.csv
This is an example unfilled sdata file that is written in the first part of the imputation script. The program uses the .csv files from the raw folder to create this dataframe and it saves it in the main directory. 
Because the sdata file is the consolidated raw precipitation data prior to imputation, there is no need to recreate it over and over again if you are not changing your station network, study period, or study region.
Because of this, the script includes an option to just use an already-made sdata file for your selected configurations if it exists. The script should fail if your configurations don't match the information listed in
the sdata file name.

The sdata file name includes 01d for the 1-day ABM values, GHCN-D_sentinel to indicate the network the data corresponds to, 1895-2024 for the study period, and 37.2N_-95.7E_d12.7x29.6 for the geographical area being studied.
The file structure is the same as the filled ABM file in the frame folder, with columns being each station and rows are each year (with the last two rows including the latitude and longitude values of the stations). 
Where a station is missing an observation, the cell is blank.

### hotdeck_script.py
This is the Python script that creates the sdata file, performs the hot deck imputation, and writes the imputed data to the frame folder. The script itself includes several comments that should aid in understanding its
structure and function.

### pca_scores_GHCN-D_30yrs.csv and pca_scores_GHCN-D_sentinel.csv
If the PC-based methods are being used, the script pulls PC scores from one of these two files depending on the donor network configuration. These values were derived from performing an R-mode PCA with every station's
temporal average of several climate variables and some geographical variables. Separate PCAs were performed for each donor network (this is detailed more in the paper discussing this work). If possible, I will add some of
the PCA work to this github. It is imperative that if you desire to use the PC-based methods, you derive your own PC scores based on your data you are using. PCA results are not transferable when changing station networks,
number of years of data, etc.

The two example files here are formatted with PC scores in each column and stations in each row.

### sentinelstations.csv
This is an example list of our sentinel station network so the program can determine which stations are in this network if we are only imputing for them. Imputation for only the sentinel stations was an integral part of our
work, but imputation can be done for any group of stations using any group of donor stations that you desire. If you have a subset of stations to impute for rather than imputing for your whole donor network, this 
would be the file to modify.
