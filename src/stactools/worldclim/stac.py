from datetime import datetime
import os
from dateutil.relativedelta import relativedelta
from pystac.extensions.base import PropertiesExtension
import pytz
import json
import logging
import rasterio
from stactools.worldclim import constants
from stactools.worldclim.constants import (WORLDCLIM_CRS, WORLDCLIM_ID, WORLDCLIM_EPSG,
                                           WORLDCLIM_TITLE, DESCRIPTION,
                                           WORLDCLIM_PROVIDER, LICENSE,
                                           LICENSE_LINK, INSTRUMENT)

import pystac
from pystac import (Collection, Asset, Extent, SpatialExtent, TemporalExtent, CatalogType,
                    MediaType)

from pystac.extensions.projection import (SummariesProjectionExtension, ProjectionExtension)
from pystac.extensions.scientific import ScientificExtension
from pystac.extensions.raster import RasterExtension, RasterBand
from pystac.extensions.file import FileExtension
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.label import (
    LabelClasses,
    LabelExtension,
    LabelTask,
    LabelType,
)
from pystac.item import Item
from pystac.summaries import Summaries
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)

def create_collection(metadata: dict):
    # Creates a STAC collection for a WorldClim dataset

    title = metadata("tiff_metadata").get("title")

    utc = pytz.utc
    year = title.split(" ")[0]
    dataset_datetime = utc.localize(datetime.strptime(
        year, "%m_%Y"))  # need this to be month_yr

    end_datetime = dataset_datetime + relativedelta(years=30)  # months 01-12

    start_datetime = dataset_datetime
    end_datetime = end_datetime

    geometry = json.loads(metadata.get("geojson_geom").get(
        "@value"))  
    bbox = Polygon(geometry.get("coordinates")[0]).bounds

    collection = pystac.Collection(
        id=WORLDCLIM_ID,
        title=WORLDCLIM_TITLE,
        description=DESCRIPTION,
        providers=[WORLDCLIM_PROVIDER],
        license=LICENSE,
        extent=pystac.Extent(
            pystac.SpatialExtent(bbox),
            pystac.TemporalExtent([start_datetime, end_datetime])),
        catalog_type=pystac.CatalogType.RELATIVE_PUBLISHED
    ),
    
    item_assets_ext = pystac.ItemAssetsExtension.ext(collection, add_if_missing=True)

    item_assets_ext.item_assets = {
        "tmin_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution Minimum temperature information "
        }),
        "tmax_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution Maximum temperature information "
        }),
        "tavg_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution average temperature information "
        }),
        "precip_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution precipitation information "
        }),
        "solarrad_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution Solar Radiation information "
        }),
        "windspeed_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution wind speed information "
        }),
        "watervap_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution water vapor pressure information "
        })
    },
    ScientificExtension({ 
        "sci:doi": "https://doi.org/10.1002/joc.5086",
        "sci:citation": "Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial resolution climate surfaces for global land areas. International Journal of Climatology 37 (12): 4302-4315.",
        "sci:publications": None,
        "doi": "https://doi.org/10.1002/joc.5086",
        "citation": "Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial resolution climate surfaces for global land areas. International Journal of Climatology 37 (12): 4302-4315."
    }),
    PropertiesExtension({
        "properties": None ,
        "version": "2.1",
        "title": "WorldClim version 2.1",
        "description": constants.DESCRIPTION,
        "datetime": dataset_datetime #get datetime info
    }),
    dataset_worldclim = rasterio.open(WORLDCLIM_TITLE)
    ProjectionExtension({
        "epsg": WORLDCLIM_EPSG,
        "wkt2": "World Geodetic System 1984",
        "projjson": WORLDCLIM_CRS #projjson object representing the CRS that bbox and geometry represent,
        "bbox": dataset_worldclim.bounds, #self defined? Bounding box of the Item in the asset CRS in 2 or 3 dimensions.
        "centroid": ''# Center      (   0.0000000,   0.0000000) (  0d 0' 0.01"E,  0d 0' 0.01"N))
        'shape': ''#[integer] Number of pixels in Y and X directions for the default grid
        "transform": ''#[number]The affine transformation coefficients for the default grid
    }),

    collection.add_link(LICENSE_LINK)

    return collection

def create_item(file: str, file_url: str, cog_href: str = None) -> pystac.Item:
    """Creates a STAC item for a WorldClim dataset.

    Args:
        metadata_url (str): Path to provider metadata.
        cog_href (str, optional): Path to COG asset.

    Returns:
        pystac.Item: STAC Item object.
    """

    title = constants.WORLDCLIM_TITLE 
    description = constants.DESCRIPTION
    instrument = constants.INSTRUMENT

    # example filename = "wc2.1_10m_01.tif"
    climate_mode = [file.spilt('_')[0]]
    gsd = [file.spilt('_')[1]]
    utc = pytz.utc
    month = os.path.splitext(file)[0].split("_")[-1]  # extracts the string after the last underscore and before the last period
    start_year = "1970"
    end_year = "2000"

    start_datestring = f"{month}_{start_year}"
    start_datetime = utc.localize(datetime.strptime(start_datestring, "%m_%Y"))
    print(start_datetime)

    end_datestring = f"{int(month) + 1}_{end_year}"
    end_datetime = utc.localize(datetime.strptime(end_datestring, "%m_%Y"))
    print(end_datetime)

    # use rasterio
    dataset_worldclim = rasterio.open(title)
    id = title.replace(" ", "-")
    # geometry = longitude/latitude
    geometry = dataset_worldclim.crs  # get geometry based on ESPG
    bbox = dataset_worldclim.bounds  # get bounding box with rastero.bounds
    properties = {"title": title, "description": description}

    # Create item
    item = pystac.Item(
        id=id,
        geometry=geometry,
        bbox=bbox,
        datetime=start_datetime,
        properties=properties,
        stac_extensions=[],
    )

    if start_datetime and end_datetime:
        item.common_metadata.start_datetime = start_datetime
        item.common_metadata.end_datetime = end_datetime

    item.ext.enable("projection")
    item.ext.projection.epsg = WORLDCLIM_EPSG

    # Create metadata asset
    item.add_asset(
        "metadata",  # check asset needs: no metadata file
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.JSON,
            roles=["metadata"],
            title="WorldClim version 2.1 metadata",
        )
    )
    # Create metadata asset
    item.add_asset(
        "tmin",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["tmin"],
            title="Minimum Temperature (°C)",
        )
    )
    item.add_asset(
        "tmax",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["tmax"],
            title="Maximum Temperature (°C)",
        )
    )
    item.add_asset(
        "tavg",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["tavg"],
            title="Average Temperature (°C)",
        )
    )
    item.add_asset(
        "precipitation",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["precipitation"],
            title="Precipitation (mm)",
        )
    )   
    item.add_asset(
        "solar radiation",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["solar radiation"],
            title="Solar Radiation (kJ m-2 day-1)",
        )
    )
    item.add_asset(
        "wind speed",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["wind speed"],
            title="Wind Speed (m s-1)",
        )
    )
    item.add_asset(
        "water vapor pressure",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["water vapor pressure"],
            title="Water Vapor Pressure (kPa)",
        )
    )
    
    if cog_href is not None(
        # Create COG asset if it exists.
        item.add_asset(
            "worldclim",
            pystac.Asset(
                href=cog_href,
                media_type=pystac.MediaType.COG,
                roles=["data"],
                title="WorldClim COGs"
            )
        )
    )
    
# Complete the projection extension
    cog_asset_projection = pystac.ProjectionExtension.ext(cog_asset, add_if_missing=True)
    cog_asset_projection.epsg = item_projection.epsg
    cog_asset_projection.bbox = item_projection.bbox
    cog_asset_projection.transform = item_projection.transform
    cog_asset_projection.shape = item_projection.shape
    
return item

#create collection for bioclim variables
#month data not stored in bioclim variables 
def create_collection(metadata: dict):
    # Creates a STAC collection for a WorldClim bioclim variables dataset

    title = metadata("tiff_metadata").get("title")

    utc = pytz.utc
    year = title.split(" ")[0]
    dataset_datetime = utc.localize(datetime.strptime(year, "%Y"))  # need this to be month_yr

    end_datetime = dataset_datetime + relativedelta(years=30)  # months 01-12

    start_datetime = dataset_datetime
    end_datetime = end_datetime

    geometry = json.loads(metadata.get("geojson_geom").get(
        "@value"))  
    bbox = Polygon(geometry.get("coordinates")[0]).bounds

    collection = pystac.Collection(
        id=WORLDCLIM_ID,
        title=WORLDCLIM_TITLE,
        description=DESCRIPTION,
        providers=[WORLDCLIM_PROVIDER],
        license=LICENSE,
        extent=pystac.Extent(
            pystac.SpatialExtent(bbox),
            pystac.TemporalExtent([start_datetime, end_datetime])),
        catalog_type=pystac.CatalogType.RELATIVE_PUBLISHED
    ),
    
    item_assets_ext = pystac.ItemAssetsExtension.ext(collection, add_if_missing=True)


    item_assets_ext.item_assets = {
        "bio_1":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO1 = Annual Mean Temperature information "
        }),
        "bio_2":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO2 = Mean Diurnal Range (Mean of monthly (max temp - min temp)) information "
        }),
        "bio_3":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO3 = Isothermality (BIO2/BIO7) (×100) information "
        }),
        "bio_4":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO4 = Temperature Seasonality (standard deviation ×100) information "
        }),
        "bio_5":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO5 = Max Temperature of Warmest Month information "
        }),
        "bio_6":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO6 = Min Temperature of Coldest Month information "
        }),
        "bio_7":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO7 = Temperature Annual Range (BIO5-BIO6) information "
        }),
        "bio_8":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO8 = Mean Temperature of Wettest Quarter information "
        }),
        "bio_9":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO9 = Mean Temperature of Driest Quarter information "
        }),
        "bio_10":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO10 = Mean Temperature of Warmest Quarter information "
        }),
        "bio_11":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO11 = Mean Temperature of Coldest Quarter information "
        }),
        "bio_12":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO12 = Annual Precipitation information "
        }),
        "bio_13":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO13 = Precipitation of Wettest Month information "
        }),
        "bio_14":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO14 = Precipitation of Driest Month information "
        }),
        "bio_15":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO15 = Precipitation Seasonality (Coefficient of Variation) information "
        }),
        "bio_16":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO16 = Precipitation of Wettest Quarter information "
        }),
        "bio_17":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO17 = Precipitation of Driest Quarter information "
        }),
        "bio_18":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO18 = Precipitation of Warmest Quarter information "
        }),
        "bio_19":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing 30s resolution BIO19 = Precipitation of Coldest Quarter information "
        })
    },
    ScientificExtension({ 
        "sci:doi": "https://doi.org/10.1002/joc.5086",
        "sci:citation": "Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial resolution climate surfaces for global land areas. International Journal of Climatology 37 (12): 4302-4315.",
        "sci:publications": None,
        "doi": "https://doi.org/10.1002/joc.5086",
        "citation": "Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial resolution climate surfaces for global land areas. International Journal of Climatology 37 (12): 4302-4315."
    }),
    PropertiesExtension({
        "properties": None,
        "version": "2.1",
        "title": "WorldClim version 2.1",
        "description": constants.DESCRIPTION,
        "datetime": dataset_datetime #get datetime info
    }),

    collection.add_link(LICENSE_LINK)

return collection

#create items for bioclim variables
def create_item(file: str, file_url: str, cog_href: str = None) -> pystac.Item:
    """Creates a STAC item for a WorldClim dataset.

    Args:
        metadata_url (str): Path to provider metadata.
        cog_href (str, optional): Path to COG asset.

    Returns:
        pystac.Item: STAC Item object.
    """

    title = constants.WORLDCLIM_TITLE 
    description = constants.DESCRIPTION
    instrument = constants.INSTRUMENT

    # example filename = "wc2.1_10m_01.tif"
    climate_mode = [file.spilt('_')[0]]
    gsd = [file.spilt('_')[1]]
    utc = pytz.utc
    month = os.path.splitext(file)[0].split("_")[-1]  # extracts the string after the last underscore and before the last period
    start_year = "1970"
    end_year = "2000"

    start_datestring = f"{month}_{start_year}"
    start_datetime = utc.localize(datetime.strptime(start_datestring, "%m_%Y"))
    print(start_datetime)

    end_datestring = f"{int(month) + 1}_{end_year}"
    end_datetime = utc.localize(datetime.strptime(end_datestring, "%m_%Y"))
    print(end_datetime)

    # use rasterio
    dataset_worldclim = rasterio.open(title)
    id = title.replace(" ", "-")
    # geometry = longitude/latitude
    geometry = dataset_worldclim.crs  # get geometry based on ESPG
    bbox = dataset_worldclim.bounds  # get bounding box with rastero.bounds
    properties = {"title": title, "description": description}

    # Create item
    item = pystac.Item(
        id=id,
        geometry=geometry,
        bbox=bbox,
        datetime=start_datetime,
        properties=properties,
        stac_extensions=[],
    )

    if start_datetime and end_datetime:
        item.common_metadata.start_datetime = start_datetime
        item.common_metadata.end_datetime = end_datetime

    item.ext.enable("projection")
    item.ext.projection.epsg = WORLDCLIM_EPSG

    # Create metadata asset
    item.add_asset(
        "metadata",  # check asset needs: no metadata file
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.JSON,
            roles=["metadata"],
            title="WorldClim version 2.1 metadata",
        )
    )
    # Create metadata asset
    item.add_asset(
        "bio_1",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO1"],
            title="BIO1 = Annual Mean Temperature information",
        )
    )
    item.add_asset(
        "bio_2",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO2"],
            title="BIO2 = Mean Diurnal Range (Mean of monthly (max temp - min temp))",
        )
    )
    item.add_asset(
        "bio_3",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO3"],
            title="BIO3 = Isothermality (BIO2/BIO7) (×100)",
        )
    )
    item.add_asset(
        "bio_4",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO4"],
            title="BIO4 = Temperature Seasonality (standard deviation ×100)",
        )
    )
    item.add_asset(
        "bio_5",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO5"],
            title="BIO5 = Max Temperature of Warmest Month",
        )
    )
    item.add_asset(
        "bio_6",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO6"],
            title="BIO6 = Min Temperature of Coldest Month",
        )
    )
    item.add_asset(
        "bio_7",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO7"],
            title="BIO7 = Temperature Annual Range (BIO5-BIO6))",
        )
    )
    item.add_asset(
        "bio_8",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO8"],
            title="BIO8 = Mean Temperature of Wettest Quarter)",
        )
    )
    item.add_asset(
        "bio_9",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO9"],
            title="BIO9 = Mean Temperature of Driest Quarter",
        )
    )
    item.add_asset(
        "bio_10",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO10"],
            title="BIO10 = Mean Temperature of Warmest Quarter",
        )
    )
    item.add_asset(
        "bio_11",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO11"],
            title="BIO11 = Mean Temperature of Coldest Quarter",
        )
    )
    item.add_asset(
        "bio_12",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO12"],
            title="BIO12 = Annual Precipitation",
        )
    )
    item.add_asset(
        "bio_13",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO13"],
            title="BIO13 = Precipitation of Wettest Month",
        )
    )
    item.add_asset(
        "bio_14",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO14"],
            title="BIO14 = Precipitation of Driest Month",
        )
    )
    item.add_asset(
        "bio_15",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO15"],
            title="BIO15 = Precipitation Seasonality (Coefficient of Variation)",
        )
    )
    item.add_asset(
        "bio_16",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO16"],
            title="BIO16 = Precipitation of Wettest Quarter",
        )
    )
    item.add_asset(
        "bio_17",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO17"],
            title="BIO17 = Precipitation of Driest Quarter",
        )
    )
    item.add_asset(
        "bio_18",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO18"],
            title="BIO18 = Precipitation of Warmest Quarter",
        )
    )
    item.add_asset(
        "bio_19",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO19"],
            title="BIO19 = Precipitation of Coldest Quarter",
        )
    )
    
    if cog_href is not None(
        # Create COG asset if it exists.
        item.add_asset(
            "worldclim",
            pystac.Asset(
                href=cog_href,
                media_type=pystac.MediaType.COG,
                roles=["data"],
                title="WorldClim BIO COGs"
            )
        )
    )
    
# Complete the projection extension
    cog_asset_projection = pystac.ProjectionExtension.ext(cog_asset, add_if_missing=True)
    cog_asset_projection.epsg = item_projection.epsg
    cog_asset_projection.bbox = item_projection.bbox
    cog_asset_projection.transform = item_projection.transform
    cog_asset_projection.shape = item_projection.shape

        # Complete the label Extension
    cog_asset.extra_fields["label:type"] = item_label.label_type
    cog_asset.extra_fields["label:tasks"] = item_label.label_tasks
    cog_asset.extra_fields[
        "label:properties"] = item_label.label_properties
     cog_asset.extra_fields[
        "label:description"] = item_label.label_description
    cog_asset.extra_fields["label:classes"] = [
        item_label.label_classes[0].to_dict()
        ]
    
return item