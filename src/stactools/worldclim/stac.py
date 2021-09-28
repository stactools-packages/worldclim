from datetime import datetime, timedelta, timezone
from typing import Optional
import calendar
import os
from pystac.extensions.base import PropertiesExtension
import pytz
import logging
import rasterio

from stactools.worldclim.constants import (
    BIOCLIM_DESCRIPTION,
    DATA_VARIABLES,
    WORLDCLIM_ID,
    WORLDCLIM_EPSG,
    WORLDCLIM_TITLE,
    DESCRIPTION,
    WORLDCLIM_PROVIDER,
    LICENSE,
    LICENSE_LINK,
    START_YEAR,
    END_YEAR,
    WORLDCLIM_FTP_bioclim,
    WORLDCLIM_VERSION,
)

import pystac
import shapely

from pystac import (Collection, Asset, Extent, SpatialExtent, TemporalExtent,
                    CatalogType, MediaType, Item)

from pystac.extensions.projection import (ProjectionExtension)
from pystac.extensions.scientific import ScientificExtension
from pystac.extensions.version import VersionExtension
from pystac.extensions.item_assets import AssetDefinition
from pystac.extensions.item_assets import ItemAssetsExtension
from stactools.core.io import ReadHrefModifier

from stactools.worldclim.enum import Month, Resolution

logger = logging.getLogger(__name__)


def create_monthly_collection() -> Collection:
    #  Creates a STAC collection for a WorldClim dataset
    #  need to pass in month data?

    utc = pytz.utc

    start_year = "1970"
    end_year = "2000"

    start_datestring = start_year
    start_datetime = utc.localize(datetime.strptime(start_datestring, "%Y"))
    print(start_datetime)

    end_datestring = end_year
    end_datetime = utc.localize(datetime.strptime(end_datestring, "%Y"))
    print(end_datetime)

    bbox = [-180., 90., 180., -90.]

    collection = Collection(id=WORLDCLIM_ID,
                            title=WORLDCLIM_TITLE,
                            description=DESCRIPTION,
                            providers=[WORLDCLIM_PROVIDER],
                            license=LICENSE,
                            extent=Extent(
                                SpatialExtent([bbox]),
                                TemporalExtent([[start_datetime,
                                                 end_datetime]])),
                            catalog_type=CatalogType.RELATIVE_PUBLISHED)

    collection.add_link(LICENSE_LINK)

    # projection extension
    collection_proj = ProjectionExtension.ext(collection, add_if_missing=True)
    collection_proj.epsg = [WORLDCLIM_EPSG],
    collection_proj.wkt2 = "World Geodetic System 1984",
    collection_proj.bbox = [-180., 90., 180., -90.],
    collection_proj.centroid = [0., 0.],
    collection_proj.shape = [4320, 8640],
    collection_proj.transform = [-180., 360., 0., 90., 0., 180.],

    # collection version
    collection_version = VersionExtension.ext(collection, add_if_missing=True)
    collection_version.latest = "WorldClim version 2.1",

    # collection scientific extension
    sci_ext = ScientificExtension.ext(collection, add_if_missing=True)
    sci_ext.doi = "https://doi.org/10.1002/joc.5086",
    sci_ext.citation = """Fick, S.E. and R.J. Hijmans, 2017. WorldClim 2: new 1km spatial
        resolution climate surfaces for global land areas. International
        Journal of Climatology 37 (12): 4302-4315.""",
    sci_ext.publications = None,

    # item assets extension
    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
    # for each month (item) assets are defined below.
    item_assets_ext.item_assets = {
        "tmin_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing Minimum temperature information "
        }),
        "tmax_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing Maximum temperature information "
        }),
        "tavg_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing average temperature information "
        }),
        "precip_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing precipitation information "
        }),
        "solarrad_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing Solar Radiation information "
        }),
        "windspeed_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing wind speed information "
        }),
        "watervap_tiff":
        AssetDefinition({
            "type":
            MediaType.TIFF,
            "roles": ["data"],
            "description":
            "TIFF containing water vapor pressure information "
        }),
    }

    return collection

def create_monthly_item(
    resolution: Resolution,
    month: Month,
    destination: str,
    cog_dir_href: str,
    cog_href_modifier: Optional[ReadHrefModifier] = None,
) -> Item:
    """Creates a STAC item for a WorldClim dataset.

    Args:
        resolution (Resolution): Desired item resolution
        month (Month): Desired item month
        destination (str): Destination directory
        cog_dir_href (str): Directory containing COGs
        cog_href_modifier (ReadHrefModifier, optional): Funtion to apply to the cog_dir_href

    Returns:
        pystac.Item: STAC Item object.
    """
    # user defined: resolution and month
    # item function creates an item of the variables in that res
    # # and month based on the file name
    # data organized in folders by month (need function to do this),
    # # search for res and variable in filename

    # example filename = "wc2.1_30s_tmin_01.tif"

    item = None
    for (data_var, data_var_desc) in DATA_VARIABLES.items():
        tiff_file_name = f"wc{WORLDCLIM_VERSION}_{resolution.value}_{data_var}_{month.value:02d}.tif"  # noqa E501
        cog_href = os.path.join(cog_dir_href, tiff_file_name)
        if cog_href_modifier:
            cog_access_href = cog_href_modifier(cog_href)
        else:
            cog_access_href = cog_href

        start_datetime = datetime(
            START_YEAR,
            month.value,
            1,
            tzinfo=timezone.utc,
        )
        end_datetime = datetime(
            END_YEAR,
            month.value + 1,
            1,
            tzinfo=timezone.utc,
        ) - timedelta(seconds=1)

        # use rasterio to open tiff file
        with rasterio.open(cog_access_href) as dataset:
            bbox = list(dataset.bounds)
            geometry = shapely.geometry.mapping(
                shapely.geometry.box(*bbox, ccw=True))
            transform = list(dataset.transform)
            shape = [dataset.height, dataset.width]

        if item is None:
            # Create item
            id = f"wc{WORLDCLIM_VERSION}_{resolution.value}_{month.value}"
            properties = {
                "title":
                f"Worldclim {resolution.value} {calendar.month_name[month.value]}",
                "description": DESCRIPTION,
            }
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

            item_projection = ProjectionExtension.ext(item,
                                                      add_if_missing=True)
            item_projection.epsg = WORLDCLIM_EPSG
            item_projection.bbox = bbox
            item_projection.transform = transform
            item_projection.shape = shape

        cog_asset = Asset(
            href=cog_href,
            media_type=MediaType.TIFF,
            roles=["data"],
            title=data_var_desc,
        )
        item.add_asset(
            data_var,
            cog_asset,
        )

        # Include projection information on Asset
        cog_asset_proj = ProjectionExtension.ext(cog_asset,
                                                 add_if_missing=True)
        cog_asset_proj.epsg = item_projection.epsg
        cog_asset_proj.transform = item_projection.transform
        cog_asset_proj.bbox = item_projection.bbox
        cog_asset_proj.shape = item_projection.shape

    assert (item is not None)
    item.set_self_href(
        os.path.join(
            destination,
            f"wc{WORLDCLIM_VERSION}_{resolution.value}_{month.value:02d}.json")
    )
    return item


# create collection for bioclim variables
# month data not stored in bioclim variables
def create_bioclim_collection() -> Collection:
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

    bbox = [-180., 90., 180., -90.]

    collection = pystac.Collection(
        id=WORLDCLIM_ID,
        title=title_bioclim,
        description=BIOCLIM_DESCRIPTION,
        providers=[WORLDCLIM_PROVIDER[WORLDCLIM_FTP_bioclim]],
        license=LICENSE,
        extent=pystac.Extent(
            pystac.SpatialExtent([bbox]),
            pystac.TemporalExtent([[start_datetime, end_datetime]])),
        catalog_type=pystac.CatalogType.RELATIVE_PUBLISHED)

    collection.add_link(LICENSE_LINK)

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
        "description": DESCRIPTION,
        # "datetime": dataset_datetime
    }),
    ProjectionExtension({
        "proj:epsg": WORLDCLIM_EPSG,
        "proj:wkt2": "World Geodetic System 1984",
        "proj:bbox": [-180, 90, 180, -90],
        "proj:centroid": [0, 0],
        'proj:shape': [4320, 8640],
        "proj:transform": [-180, 360, 0, 90, 0, 180]
    })

    return collection


# create items for bioclim variables
def create_bioclim_item(resolution_href: str, directory_loc: os.path) -> Item:
    """Creates a STAC item for a WorldClim Bioclimatic dataset.

    Args:
        resolution_href (str): Desired item resolution
        directory_loc (os.path) : Local path to dataset

    Returns:
        pystac.Item: STAC Item object.
    """
    # item = resolution
    # assets = bioclim variables

    title = 'Worldclim Bioclimatic Variables'
    description = BIOCLIM_DESCRIPTION

    bioclim_variables_dict = {
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

    for key in bioclim_variables_dict.keys():

        tiff_href = "wc2.1_" + resolution_href + "_" + key + ".tif"
        # example filename = "wc2.1_5m_bio_1.tif"

        utc = pytz.utc
        # extracts the string after the last underscore and before the last period
        start_year = "1970"
        end_year = "2000"

        start_datestring = f"{start_year}"
        start_datetime = utc.localize(datetime.strptime(
            start_datestring, "%Y"))
        print(start_datetime)

        end_datestring = f"{end_year}"
        end_datetime = utc.localize(datetime.strptime(end_datestring, "%Y"))
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
                }  # does this have to match website?

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

        # tiff_href = "wc2.1_"+resolution_href+"_"+key+".tif" # file structure defined above
        tiff_file_path = open(directory_loc + "/" + tiff_href)

        # Create asset based on keys in variables_dict
        item.add_asset(
            key,
            Asset(
                href=tiff_file_path,
                media_type=MediaType.TIFF,
                roles=["data"],
                title=bioclim_variables_dict[key],
            ))
        tiff_file_path.close()

    # Include projection information
    proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
    proj_ext.epsg = item_projection.epsg
    proj_ext.transform = item_projection.transform
    proj_ext.bbox = item_projection.bbox
    proj_ext.wkt2 = item_projection.wkt2
    proj_ext.shape = item_projection.shape
    proj_ext.centroid = item_projection.centroid

    return item
