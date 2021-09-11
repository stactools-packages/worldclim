# stactools-package

stactools worldclim
Name: worldclim
Package: stactools.worldclim
PyPI: https://pypi.org/project/stactools-worldclim/
Owner: @sparkgeo
Dataset homepage: WorldClim
STAC extensions used:

version
scientific
projection 
item assets

This is WorldClim version 2.1 climate data for 1970-2000. This version was released in January 2020. There are monthly climate data for minimum, mean, and maximum temperature, precipitation, solar radiation, wind speed, water vapor pressure, and for total precipitation. There are also 19 “bioclimatic” variables. The data is available at the four spatial resolutions, between 30 seconds (~1 km2) to 10 minutes (~340 km2). Each download is a “zip” file containing 12 GeoTiff (.tif) files, one for each month of the year (January is 1; December is 12).

Weather station data from between 9000 and 60 000 weather stations were interpolated using thin-plate splines with covariates including elevation, distance to the coast and three satellite-derived covariates: maximum and minimum land surface temperature as well as cloud cover, obtained with the MODIS satellite platform

Usage
Using the CLI
# Create a COG - creates /path/to/local_cog.tif
stac worldclim create-cog -d "/path/to/directory" -s "/path/to/local.tif"
# Create extent asset
worldclim create-extent-asset -d "/path/to/directory"
# Create a STAC Item - creates /path/to/directory/local_cog.json
stac worldclim create-item -d "/path/to/directory" -c "/path/to/local_cog.tif" -e "/path/to/extent.geojson"
# STAC Collection
stac worldclim create-collection -d "/path/to/directory"
As a python module
from stactools.worldclim.constants import JSONLD_HREF
from stactools.worldclim import utils, cog, stac

# Read metadata
metadata = utils.get_metadata(JSONLD_HREF)

# Create a STAC Collection
json_path = os.path.join(tmp_dir, "/path/to/worldclim.json")
stac.create_collection(metadata, json_path)

# Create a COG
cog.create_cog("/path/to/local.tif", "/path/to/cog.tif")

# Create a STAC Item
stac.create_item(metadata, "/path/to/item.json", "/path/to/cog.tif")

