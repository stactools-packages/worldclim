from datetime import datetime
import os
from pystac.extensions.base import PropertiesExtension
import pytz
import logging
import rasterio
from stactools.worldclim import constants
from stactools.worldclim.constants import (BIOCLIM_DESCRIPTION, WORLDCLIM_CRS,
                                           WORLDCLIM_ID, WORLDCLIM_EPSG,
                                           WORLDCLIM_TITLE, DESCRIPTION,
                                           WORLDCLIM_PROVIDER, LICENSE,
                                           LICENSE_LINK, WORLDCLIM_FTP_bioclim)

import pystac
from pystac import (Collection, Asset, Extent, SpatialExtent, TemporalExtent,
                    CatalogType, MediaType, Item)

from pystac.extensions.projection import (ProjectionExtension)
from pystac.extensions.scientific import ScientificExtension
from pystac.extensions.item_assets import AssetDefinition
from pystac.extensions.item_assets import ItemAssetsExtension

logger = logging.getLogger(__name__)


def create_collection() -> Collection:
    # Creates a STAC collection for a WorldClim dataset
    # need to pass in month data?

    utc = pytz.utc

    start_year = "1970"
    end_year = "2000"

    start_datestring = start_year
    start_datetime = utc.localize(datetime.strptime(start_datestring, "%Y%"))
    print(start_datetime)

    end_datestring = end_year
    end_datetime = utc.localize(datetime.strptime(end_datestring, "%Y%"))
    print(end_datetime)

    bbox = [-180, 90, 180, -90]

    collection = Collection(id=WORLDCLIM_ID,
                            title=WORLDCLIM_TITLE,
                            description=DESCRIPTION,
                            providers=[WORLDCLIM_PROVIDER],
                            license=LICENSE,
                            extent=Extent(
                                SpatialExtent(bbox),
                                TemporalExtent([start_datetime,
                                                end_datetime])),
                            catalog_type=CatalogType.RELATIVE_PUBLISHED),

    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)

    #for each month (item) assets are defined below.
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
        "sci:doi":
        "https://doi.org/10.1002/joc.5086",
        "sci:citation":
        """Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial
        resolution climate surfaces for global land areas. International
        Journal of Climatology 37 (12): 4302-4315.""",
        "sci:publications":
        None,
        "doi":
        "https://doi.org/10.1002/joc.5086",
        "citation":
        """Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial
        resolution climate surfaces for global land areas. International
        Journal of Climatology 37 (12): 4302-4315."""
    }),
    PropertiesExtension({
        "properties": None,
        "version": "2.1",
        "title": "WorldClim version 2.1",
        "description": constants.DESCRIPTION,
        # "datetime": dataset_datetime
    }),
    ProjectionExtension({
        "proj:epsg": WORLDCLIM_EPSG,
        "proj:wkt2": "World Geodetic System 1984",
        "proj:projjson": WORLDCLIM_CRS,
        "proj:bbox": [-180, 90, 180, -90],
        "proj:centroid": [0, 0],
        'proj:shape': [4320, 8640],
        "proj:transform": [-180, 360, 0, 90, 0, 180]
    }),

    collection.add_link(LICENSE_LINK)

    return collection


def create_item(tiff_href: str, file_url: str, cog_href: str = None) -> Item:
    """Creates a STAC item for a WorldClim dataset.

    Args:
        metadata_url (str): Path to provider metadata.
        cog_href (str, optional): Path to COG asset.

    Returns:
        pystac.Item: STAC Item object.
    """

    title = constants.WORLDCLIM_TITLE
    description = constants.DESCRIPTION

    # example filename = "wc2.1_30s_tmin_01.tif"
    gsd = [tiff_href.spilt('_')[1]]  #resolution
    utc = pytz.utc
    # month extracts the string after the last underscore and before the last period
    month = os.path.splitext(tiff_href)[0].split("_")[-1]  #sort based on this
    start_year = "1970"
    end_year = "2000"

    start_datestring = f"{month}_{start_year}"
    start_datetime = utc.localize(datetime.strptime(start_datestring, "%m_%Y"))
    print(start_datetime)

    end_datestring = f"{int(month) + 1}_{end_year}"
    end_datetime = utc.localize(datetime.strptime(end_datestring, "%m_%Y"))
    print(end_datetime)

    # use rasterio to open tiff file
    if tiff_href is not None:
        with rasterio.open(tiff_href) as dataset_worldclim:
            id = title.replace(" ", "-")
            # get geometry based on ESPG
            geometry = dataset_worldclim.crs
            # get bounding box with rastero.bounds
            bbox = dataset_worldclim.bounds
            properties = {"title": title, "description": description}

# Create item
    item = Item(
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

    item_projection = ProjectionExtension.ext(item, add_if_missing=True)
    item_projection.epsg = WORLDCLIM_EPSG
    if cog_href is not None:
        with rasterio.open(cog_href) as dataset:
            item_projection.bbox = list(dataset.bounds)
            item_projection.transform = list(dataset.transform)
            item_projection.shape = [dataset.height,
                                     dataset.width]  #check this

# Create metadata asset for each month
#make sure it is for the 30s resolution, or include all resolutions?
# if gsd == '30s':
#     sort by month (month = os.path.splitext(tiff_href)[0].split("_")[-1]):
        item.add_asset(
            "metadata",
            Asset(
                href=file_url,
                media_type=MediaType.JSON,
                roles=["metadata"],
                title="WorldClim version 2.1 metadata",
            ))
        # Create metadata asset
        item.add_asset(
            "tmin",
            Asset(
                href=file_url,
                media_type=MediaType.TIFF,
                roles=["tmin"],
                title="Minimum Temperature (°C)",
            ))
        item.add_asset(
            "tmax",
            Asset(
                href=file_url,
                media_type=MediaType.TIFF,
                roles=["tmax"],
                title="Maximum Temperature (°C)",
            ))
        item.add_asset(
            "tavg",
            Asset(
                href=file_url,
                media_type=MediaType.TIFF,
                roles=["tavg"],
                title="Average Temperature (°C)",
            ))
        item.add_asset(
            "precipitation",
            Asset(
                href=file_url,
                media_type=MediaType.TIFF,
                roles=["precipitation"],
                title="Precipitation (mm)",
            ))
        item.add_asset(
            "solar radiation",
            Asset(
                href=file_url,
                media_type=MediaType.TIFF,
                roles=["solar radiation"],
                title="Solar Radiation (kJ m-2 day-1)",
            ))
        item.add_asset(
            "wind speed",
            Asset(
                href=file_url,
                media_type=MediaType.TIFF,
                roles=["wind speed"],
                title="Wind Speed (m s-1)",
            ))
        item.add_asset(
            "water vapor pressure",
            Asset(
                href=file_url,
                media_type=MediaType.TIFF,
                roles=["water vapor pressure"],
                title="Water Vapor Pressure (kPa)",
            ))

        if cog_href is not None:
            # Create COG asset if it exists.
            item.add_asset("worldclim",
                           cog_asset=Asset(href=cog_href,
                                           media_type=MediaType.COG,
                                           roles=["data"],
                                           title="WorldClim COGs"))

# Include projection information
    proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
    proj_ext.epsg = item_projection.epsg
    proj_ext.transform = item_projection.transform
    proj_ext.bbox = item_projection.bbox
    proj_ext.wkt2 = item_projection.wkt2
    proj_ext.shape = item_projection.shape
    proj_ext.centroid = item_projection.centroid

    return item


#create collection for bioclim variables
#month data not stored in bioclim variables
def create_collection() -> Collection:
    # Creates a STAC collection for a WorldClim bioclim variables dataset

    title_bioclim = 'Worldclim Bioclimatic Variables'

    utc = pytz.utc
    start_year = "1970"
    end_year = "2000"

    start_datestring = start_year
    start_datetime = utc.localize(datetime.strptime(start_datestring, "%Y%"))
    print(start_datetime)

    end_datestring = end_year
    end_datetime = utc.localize(datetime.strptime(end_datestring, "%Y%"))
    print(end_datetime)

    bbox = [-180, 90, 180, -90]

    collection = pystac.Collection(
        id=WORLDCLIM_ID,
        title=title_bioclim,
        description=BIOCLIM_DESCRIPTION,
        providers=[WORLDCLIM_PROVIDER[WORLDCLIM_FTP_bioclim]],
        license=LICENSE,
        extent=pystac.Extent(
            pystac.SpatialExtent(bbox),
            pystac.TemporalExtent([start_datetime, end_datetime])),
        catalog_type=pystac.CatalogType.RELATIVE_PUBLISHED),

    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)

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
            """TIFF containing 30s resolution BIO2 = Mean Diurnal Range
            (Mean of monthly (max temp - min temp)) information """
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
            """TIFF containing 30s resolution BIO4 = Temperature Seasonality
            (standard deviation ×100) information """
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
            """TIFF containing 30s resolution BIO7 = Temperature Annual Range
            (BIO5-BIO6) information """
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
            """TIFF containing 30s resolution BIO10 = Mean Temperature
            of Warmest Quarter information """
        }),
        "bio_11":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            """TIFF containing 30s resolution BIO11 = Mean
            Temperature of Coldest Quarter information """
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
            """TIFF containing 30s resolution BIO15 = Precipitation Seasonality
            (Coefficient of Variation) information """
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
        "sci:doi":
        "https://doi.org/10.1002/joc.5086",
        "sci:citation":
        """Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial resolution climate surfaces
        for global land areas. International Journal of Climatology 37 (12): 4302-4315.""",
        "sci:publications":
        None,
        "doi":
        "https://doi.org/10.1002/joc.5086",
        "citation":
        """Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial resolution climate surfaces
        for global land areas. International Journal of Climatology 37 (12): 4302-4315."""
    }),
    PropertiesExtension({
        "properties": None,
        "version": "2.1",
        "title": "WorldClim version 2.1",
        "description": constants.DESCRIPTION,
        # "datetime": dataset_datetime
    }),
    ProjectionExtension({
        "proj:epsg": WORLDCLIM_EPSG,
        "proj:wkt2": "World Geodetic System 1984",
        "proj:projjson": WORLDCLIM_CRS,
        "proj:bbox": [-180, 90, 180, -90],
        "proj:centroid": [0, 0],
        'proj:shape': [4320, 8640],
        "proj:transform": [-180, 360, 0, 90, 0, 180]
    })

    collection.add_link(LICENSE_LINK)

    return collection


#create items for bioclim variables
def create_item(tiff_href: str, file_url: str, cog_href: str = None) -> Item:
    """Creates a STAC item for a WorldClim Bioclimatic dataset.

    Args:
        metadata_url (str): Path to provider metadata.
        cog_href (str, optional): Path to COG asset.

    Returns:
        pystac.Item: STAC Item object.
    """

    title = 'Worldclim Bioclimatic Variables'
    description = constants.BIOCLIM_DESCRIPTION

    # example filename = "wc2.1_5m_bio_1.tif"
    gsd = [tiff_href.spilt('_')[1]]  #resolution
    utc = pytz.utc
    month = os.path.splitext(tiff_href)[0].split("_")[-1]
    # extracts the string after the last underscore and before the last period
    start_year = "1970"
    end_year = "2000"

    start_datestring = f"{month}_{start_year}"
    start_datetime = utc.localize(datetime.strptime(start_datestring, "%m_%Y"))
    print(start_datetime)

    end_datestring = f"{int(month) + 1}_{end_year}"
    end_datetime = utc.localize(datetime.strptime(end_datestring, "%m_%Y"))
    print(end_datetime)

    # use rasterio
    if tiff_href is not None:
        with rasterio.open(tiff_href) as dataset_worldclim:
            id = title.replace(" ", "-")
            # geometry = longitude/latitude - get geom based on EPSG
            geometry = dataset_worldclim.crs
            bbox = dataset_worldclim.bounds
            # get bounding box with rastero.bounds
            properties = {
                "title": title,
                "description": description
            }  #does this have to match website?

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

    item_projection = ProjectionExtension.ext(item, add_if_missing=True)
    item_projection.epsg = WORLDCLIM_EPSG
    if cog_href is not None:
        with rasterio.open(cog_href) as dataset:
            item_projection.bbox = list(dataset.bounds)
            item_projection.transform = list(dataset.transform)
            item_projection.shape = [dataset.height,
                                     dataset.width]  #check this


# Create metadata asset
    item.add_asset(
        "metadata",  # check asset needs: no metadata file
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["metadata"],
                     title="WorldClim version 2.1 metadata"))
    # Create metadata asset
    item.add_asset(
        "bio_1",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO1"],
                     title="BIO1 = Annual Mean Temperature information"))
    item.add_asset(
        "bio_2",
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO2"],
            title=
            "BIO2 = Mean Diurnal Range (Mean of monthly (max temp - min temp))"
        ))
    item.add_asset(
        "bio_3",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO3"],
                     title="BIO3 = Isothermality (BIO2/BIO7) (×100)"))
    item.add_asset(
        "bio_4",
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO4"],
            title="BIO4 = Temperature Seasonality (standard deviation ×100)"))
    item.add_asset(
        "bio_5",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO5"],
                     title="BIO5 = Max Temperature of Warmest Month"))
    item.add_asset(
        "bio_6",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO6"],
                     title="BIO6 = Min Temperature of Coldest Month"))
    item.add_asset(
        "bio_7",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO7"],
                     title="BIO7 = Temperature Annual Range (BIO5-BIO6))"))
    item.add_asset(
        "bio_8",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO8"],
                     title="BIO8 = Mean Temperature of Wettest Quarter)"))
    item.add_asset(
        "bio_9",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO9"],
                     title="BIO9 = Mean Temperature of Driest Quarter"))
    item.add_asset(
        "bio_10",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO10"],
                     title="BIO10 = Mean Temperature of Warmest Quarter"))
    item.add_asset(
        "bio_11",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO11"],
                     title="BIO11 = Mean Temperature of Coldest Quarter"))
    item.add_asset(
        "bio_12",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO12"],
                     title="BIO12 = Annual Precipitation"))
    item.add_asset(
        "bio_13",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO13"],
                     title="BIO13 = Precipitation of Wettest Month"))
    item.add_asset(
        "bio_14",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO14"],
                     title="BIO14 = Precipitation of Driest Month"))
    item.add_asset(
        "bio_15",
        pystac.Asset(
            href=file_url,
            media_type=pystac.MediaType.TIFF,
            roles=["BIO15"],
            title="BIO15 = Precipitation Seasonality (Coefficient of Variation)"
        ))
    item.add_asset(
        "bio_16",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO16"],
                     title="BIO16 = Precipitation of Wettest Quarter"))
    item.add_asset(
        "bio_17",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO17"],
                     title="BIO17 = Precipitation of Driest Quarter"))
    item.add_asset(
        "bio_18",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO18"],
                     title="BIO18 = Precipitation of Warmest Quarter"))
    item.add_asset(
        "bio_19",
        pystac.Asset(href=file_url,
                     media_type=pystac.MediaType.TIFF,
                     roles=["BIO19"],
                     title="BIO19 = Precipitation of Coldest Quarter"))

    if cog_href is not None:
        # Create COG asset if it exists.
        item.add_asset("worldclim",
                       cog_asset=pystac.Asset(href=cog_href,
                                              media_type=pystac.MediaType.COG,
                                              roles=["data"],
                                              title="WorldClim BIO COGs"))

    # Include projection information
    proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
    proj_ext.epsg = item_projection.epsg
    proj_ext.transform = item_projection.transform
    proj_ext.bbox = item_projection.bbox
    proj_ext.wkt2 = item_projection.wkt2
    proj_ext.shape = item_projection.shape
    proj_ext.centroid = item_projection.centroid

    return item
