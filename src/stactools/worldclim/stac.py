from datetime import datetime
import os
from dateutil.relativedelta import relativedelta
import pytz
import json
import logging
import rasterio
from stactools.worldclim import constants
from stactools.worldclim.constants import (WORLDCLIM_ID, WORLDCLIM_EPSG,
                                           WORLDCLIM_TITLE, DESCRIPTION,
                                           WORLDCLIM_PROVIDER, LICENSE,
                                           LICENSE_LINK, INSTRUMENT)

import pystac
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)

def create_collection(metadata: dict):
    # Creates a STAC collection for a WorldClim dataset

    title = metadata.("tiff_metadata").get("title")

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
        catalog_type=pystac.CatalogType.RELATIVE_PUBLISHED,
    ​
    item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
​
    item_assets.item_assets = {
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
    "sci:doi": "https://doi.org/10.1002/joc.5086",
    "sci:citation": "Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial resolution climate surfaces for global land areas. International Journal of Climatology 37 (12): 4302-4315.",
    "sci:publications": [
    {
      "doi": "https://doi.org/10.1002/joc.5086",
      "citation": "Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial resolution climate surfaces for global land areas. International Journal of Climatology 37 (12): 4302-4315."
    },
    
    "properties": {
    "version": "2.1",
    "title": "WorldClim version 2.1",
    "description": constants.DESCRIPTION
    "datetime": "" #get datetime info
    },

    )
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
        ),
    )
    # Create metadata asset
    item.add_asset(
        "tmin",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["tmin"],
            title="Minimum Temperature (°C)",
        ),

    item.add_asset(
        "tmax",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["tmax"],
            title="Maximum Temperature (°C)",
        ),

    item.add_asset(
        "tavg",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["tavg"],
            title="Average Temperature (°C)",
        ),

    item.add_asset(
        "precipitation",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["precipitation"],
            title="Precipitation (mm)",
        ),

    item.add_asset(
        "solar radiation",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["solar radiation"],
            title="Solar Radiation (kJ m-2 day-1)",
        ),

    item.add_asset(
        "wind speed",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["wind speed"],
            title="Wind Speed (m s-1)",
        ),

    item.add_asset(
        "water vapor pressure",  
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["water vapor pressure"],
            title="Water Vapor Pressure (kPa)",
        ),

    if cog_href is not None:
        # Create COG asset if it exists.
        item.add_asset(
            "worldclim",
            pystac.Asset(
                href=cog_href,
                media_type=pystac.MediaType.COG,
                roles=["data"],
                title="WorldClim COGs",
            ),
        )

    if start_datetime and end_datetime:
        item.common_metadata.start_datetime = start_datetime
        item.common_metadata.end_datetime = end_datetime

    item.ext.enable("projection")
    item.ext.projection.epsg = WORLDCLIM_EPSG

    ]
    # Projection Extension: taken from nrcan landcover script, might need to change
    cog_asset_projection = ProjectionExtension.ext(cog_asset,
                                                       add_if_missing=True)
    cog_asset_projection.epsg = item_projection.epsg
    cog_asset_projection.bbox = item_projection.bbox
    cog_asset_projection.transform = item_projection.transform
    cog_asset_projection.shape = item_projection.shape
#  Label Extension (doesn't seem to handle Assets properly)
    cog_asset.extra_fields["label:type"] = item_label.label_type
    cog_asset.extra_fields["label:tasks"] = item_label.label_tasks
    cog_asset.extra_fields["label:properties"] = item_label.label_properties
    cog_asset.extra_fields["label:description"] = item_label.label_description
    cog_asset.extra_fields["label:classes"] = [
    item_label.label_classes[0].to_dict()
    ]
    
    return item

#create collection for bioclim variables
#bioclim item: 19 bioclim assets (https://worldclim.org/data/bioclim.html)
