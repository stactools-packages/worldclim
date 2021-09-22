import ftplib
import zipfile
from stactools.worldclim.constants import (WORLDCLIM_FTP_tmin, WORLDCLIM_FTP_tmax, WORLDCLIM_FTP_tavg,
                                           WORLDCLIM_FTP_precip, WORLDCLIM_FTP_rad, WORLDCLIM_FTP_wind,
                                           WORLDCLIM_FTP_vap, WORLDCLIM_FTP_bioclim, WORLDCLIM_FTP_elev)

# function to download dataset and unzip to store locally
# information acessed through item definition
# items will access the folder the dataset was downloaded,
## and search for user defined resolution and month to get asset variables
# user defined local directory

def dataset_download(local_dir:str, ftp_path:list):
    # download dataset variable of interest
    for link in ftp_path:
        ftplib.FTP(link)
        # unzip and save to local dir
        zipfile(link, local_dir) # maybe this

        with zipfile.ZipFile(link,'r') as z: # maybe this
            z.extractall()

dataset_download(local_dir=str,ftp_path=WORLDCLIM_FTP_tmin) #do this for all folders
print("done")
