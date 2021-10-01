from pyproj import CRS
from pystac import Link, Provider
from pystac.provider import ProviderRole

WORLDCLIM_ID = "world-clim"
WORLDCLIM_VERSION = 2.1
WORLDCLIM_EPSG = 4326
WORLDCLIM_CRS_WKT = CRS.from_epsg(WORLDCLIM_EPSG).to_wkt()
WORLDCLIM_TITLE = "Historical climate data"
LICENSE = "CC-BY-SA-4.0"
title_string = "Creative Commons - Attribution-ShareAlike 4.0 International - CC BY-SA 4.0"
LICENSE_LINK = Link(rel="license",
                    target="https://creativecommons.org/licenses/by-sa/4.0/",
                    title=title_string)

DESCRIPTION = """This is WorldClim version 2.1 climate data for 1970-2000. This version was
released in January 2020. There are monthly climate data for minimum, mean, and maximum temperature,
precipitation, solar radiation, wind speed, water vapor pressure, and for total precipitation. There
are also 19 “bioclimatic” variables. The data is available at the four spatial resolutions, between
30 seconds (~1 km2) to 10 minutes (~340 km2). Each download is a “zip” file containing 12 GeoTiff
(.tif) files, one for each month of the year (January is 1; December is 12)."""
# more metadata
INSTRUMENT = """ Weather station data from between 9000 and 60 000 weather stations were interpolated
using thin-plate splines with covariates including elevation, distance to the coast and three
satellite- derived covariates: maximum and minimum land surface temperature as well as cloud cover,
obtained with the MODIS satellite platform"""

DOI = "10.1002/joc.5086"  # https://doi.org/10.1002/joc.5086
CITATION = "Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial resolution climate surfaces for global land areas. International Journal of Climatology 37 (12): 4302-4315."  # noqa E501

START_YEAR = 1970
END_YEAR = 2000

DATASET_URL_MAIN = "https://biogeo.ucdavis.edu/data/worldclim"
DATASET_URL_TEMPLATE = f"{DATASET_URL_MAIN}/v{WORLDCLIM_VERSION}/base/wc{WORLDCLIM_VERSION}_{{resolution}}_{{variable}}.zip"  # noqa E501

WORLDCLIM_PROVIDER = Provider(
    name="WorldClim",
    roles=[ProviderRole.PROCESSOR, ProviderRole.HOST],
    url="https://worldclim.org/data/worldclim21.html")

BIOCLIM_DESCRIPTION = """Bioclimatic variables are derived from the monthly temperature
and rainfall values in order to generate more biologically meaningful variables. These are
often used in species distribution modeling and related ecological modeling techniques.
The bioclimatic variables represent annual trends (e.g., mean annual temperature, annual
precipitation) seasonality (e.g., annual range in temperature and precipitation) and extreme
or limiting environmental factors (e.g., temperature of the coldest and warmest month, and
precipitation of the wet and dry quarters). A quarter is a period of three months
(1/4 of the year)."""

MONTHLY_DATA_VARIABLES = {
    "tmin": "Minimum Temperature (degrees C)",
    "tmax": "Maximum Temperature (degrees C)",
    "tavg": "Average Temperature (degrees C)",
    "prec": "Precipitation (mm)",
    "srad": "Solar Radiation (kJ m-2 day-1)",
    "wind": "Wind Speed (m s-1)",
    "vapr": "Water Vapor Pressure (kPa)"
}

BIOCLIM_VARIABLES = {
    "bio_1": "Annual Mean Temperature",
    "bio_2": "Mean Diurnal Range (Mean of monthly (max temp - min temp))",
    "bio_3": "Isothermality (BIO2/BIO7) (×100)",
    "bio_4": "Temperature Seasonality (standard deviation ×100)",
    "bio_5": "Max Temperature of Warmest Month",
    "bio_6": "Min Temperature of Coldest Month",
    "bio_7": "Temperature Annual Range (BIO5-BIO6)",
    "bio_8": "Mean Temperature of Wettest Quarter",
    "bio_9": "Mean Temperature of Driest Quarter",
    "bio_10": "Mean Temperature of Warmest Quarter",
    "bio_11": "Mean Temperature of Coldest Quarter",
    "bio_12": "Annual Precipitation",
    "bio_13": "Precipitation of Wettest Month",
    "bio_14": "Precipitation of Driest Month",
    "bio_15": "Precipitation Seasonality (Coefficient of Variation)",
    "bio_16": "Precipitation of Wettest Quarter",
    "bio_17": "Precipitation of Driest Quarter",
    "bio_18": "Precipitation of Warmest Quarter",
    "bio_19": "Precipitation of Coldest Quarter",
}

TILING_PIXEL_SIZE = (10800, 10800)
