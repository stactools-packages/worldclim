# flake8: noqa
#input information from the abstract here

from pyproj import CRS
from pystac import Provider
from pystac import Link

WORLDCLIM_ID = "world-clim"
WORLDCLIM_EPSG = 4326  #to find  from a tiff file: gdalinfo file_path
WORLDCLIM_CRS = CRS.from_epsg(WORLDCLIM_EPSG)
WORLDCLIM_TITLE = "Historical climate data"
LICENSE = "CC-BY-SA-4.0"
LICENSE_LINK = Link(
    rel="license",
    target="https://creativecommons.org/licenses/by-sa/4.0/",
    title=
    "Creative Commons - Attribution-ShareAlike 4.0 International - CC BY-SA 4.0"
)

DESCRIPTION = "This is WorldClim version 2.1 climate data for 1970-2000. This version was released in January 2020. There are monthly climate data for minimum, mean, and maximum temperature, precipitation, solar radiation, wind speed, water vapor pressure, and for total precipitation. There are also 19 “bioclimatic” variables. The data is available at the four spatial resolutions, between 30 seconds (~1 km2) to 10 minutes (~340 km2). Each download is a “zip” file containing 12 GeoTiff (.tif) files, one for each month of the year (January is 1; December is 12)."

WORLDCLIM_PROVIDER = Provider(
    name="WorldClim",
    roles=["processor", "host"],
    url="https://worldclim.org/data/worldclim21.html")

WORLDCLIM_FTP_tmin = [
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_10m_tmin.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_5m_tmin.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_tmin.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_30s_tmin.zip"
]
WORLDCLIM_FTP_tmax = [
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_10m_tmax.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_5m_tmax.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_tmax.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_30s_tmax.zip"
]
WORLDCLIM_FTP_tavg = [
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_10m_tavg.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_5m_tavg.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_tavg.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_30s_tavg.zip"
]
WORLDCLIM_FTP_precip = [
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_10m_prec.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_5m_prec.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_prec.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_30s_prec.zip"
]
WORLDCLIM_FTP_rad = [
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_10m_srad.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_5m_srad.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_srad.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_30s_srad.zip"
]
WORLDCLIM_FTP_wind = [
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_10m_wind.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_5m_wind.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_wind.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_30s_wind.zip"
]
WORLDCLIM_FTP_vap = [
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_10m_vapr.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_5m_srad.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_srad.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_30s_srad.zip"
]
WORLDCLIM_FTP_bioclim = [
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_10m_bio.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_5m_bio.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_bio.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_30s_bio.zip"
]
WORLDCLIM_FTP_elev = [
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_10m_elev.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_5m_elev.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_elev.zip",
    "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_30s_elev.zip"
]  #list of all links

#metadata from article abstract
#spatial res = 1km2
#data included: tavg, tmin, tmax
#temporal range: 1970-2000
#elevation
#distance to coast
#max/min land surface temp, cloud cover
#global cross-validation correlations: 0.99 for temp and humidity
# 0.86 for precip
# 0.76 for wind speed
