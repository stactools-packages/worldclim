import calendar
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import pystac
import pytz
import rasterio
import shapely
from pystac import (
    Asset,
    CatalogType,
    Collection,
    Extent,
    Item,
    MediaType,
    SpatialExtent,
    TemporalExtent,
)
from pystac.extensions.base import PropertiesExtension
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.scientific import ScientificExtension
from pystac.extensions.version import VersionExtension
from stactools.core.io import ReadHrefModifier

from stactools.worldclim.constants import (
    BIOCLIM_DESCRIPTION,
    BIOCLIM_VARIABLES,
    CITATION,
    DESCRIPTION,
    DOI,
    END_YEAR,
    LICENSE,
    LICENSE_LINK,
    MONTHLY_DATA_VARIABLES,
    START_YEAR,
    WORLDCLIM_CRS_WKT,
    WORLDCLIM_EPSG,
    WORLDCLIM_ID,
    WORLDCLIM_PROVIDER,
    WORLDCLIM_TITLE,
    WORLDCLIM_VERSION,
)
from stactools.worldclim.enum import Month, Resolution

logger = logging.getLogger(__name__)


def create_monthly_collection() -> Collection:
    #  Creates a STAC collection for a WorldClim dataset

    start_datetime = datetime(
        START_YEAR,
        1,
        1,
        tzinfo=timezone.utc,
    )
    end_datetime = datetime(
        END_YEAR + 1,
        1,
        1,
        tzinfo=timezone.utc,
    ) - timedelta(seconds=1)  # type: Optional[datetime]

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
    collection_proj = ProjectionExtension.summaries(collection,
                                                    add_if_missing=True)
    collection_proj.epsg = [WORLDCLIM_EPSG]

    # version extension
    collection_version = VersionExtension.ext(collection, add_if_missing=True)
    collection_version.version = str(WORLDCLIM_VERSION)

    # item scientific extension
    sci_ext = ScientificExtension.ext(collection, add_if_missing=True)
    sci_ext.doi = DOI
    sci_ext.citation = CITATION

    # item assets extension
    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_ext.item_assets = {
        var_name: AssetDefinition({
            "title": var_name,
            "description": var_desc,
            "type": MediaType.TIFF,
            "roles": ["data"],
        })
        for (var_name, var_desc) in MONTHLY_DATA_VARIABLES.items()
    }

    return collection


def create_monthly_item(
    destination: str,
    cog_href: str,
    cog_href_modifier: Optional[ReadHrefModifier] = None,
) -> Item:
    """Creates a STAC item for a WorldClim dataset.

    Args:
        destination (str): Destination directory
        cog_dir_href (str): Directory containing COGs
        cog_href_modifier (ReadHrefModifier, optional): Funtion to apply to the cog_dir_href

    Returns:
        pystac.Item: STAC Item object.
    """

    match = re.match(rf".*{WORLDCLIM_VERSION}_(.*)_(.*)_(\d\d).*\.tif",
                     os.path.basename(cog_href))
    if match is None:
        raise ValueError("Could not extract necessary values from {cog_href}")
    res, _, m = match.groups()
    resolution = Resolution(res)
    month = Month(int(m))

    item = None
    for (data_var, data_var_desc) in MONTHLY_DATA_VARIABLES.items():
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
        if month is Month.DECEMBER:
            end_datetime = datetime(
                END_YEAR + 1,
                1,
                1,
                tzinfo=timezone.utc,
            ) - timedelta(seconds=1)
        else:
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
            item_projection.wkt2 = WORLDCLIM_CRS_WKT
            item_projection.bbox = bbox
            item_projection.transform = transform
            item_projection.shape = shape

        cog_asset = Asset(
            title=data_var,
            description=data_var_desc,
            media_type=MediaType.TIFF,
            roles=["data"],
            href=cog_href,
        )
        item.add_asset(data_var, cog_asset)

        # Include projection information on Asset
        cog_asset_proj = ProjectionExtension.ext(cog_asset,
                                                 add_if_missing=True)
        cog_asset_proj.epsg = item_projection.epsg
        cog_asset_proj.wkt2 = item_projection.wkt2
        cog_asset_proj.transform = item_projection.transform
        cog_asset_proj.bbox = item_projection.bbox
        cog_asset_proj.shape = item_projection.shape

    assert (item is not None)

    # scientific extension
    sci_ext = ScientificExtension.ext(item, add_if_missing=True)
    sci_ext.doi = DOI
    sci_ext.citation = CITATION

    item.set_self_href(
        os.path.join(destination,
                     os.path.basename(cog_href).replace(".tif", ".json")))

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
    PropertiesExtension({  # version
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
def create_bioclim_item( destination: str,
    cog_href: str,
    cog_href_modifier: Optional[ReadHrefModifier] = None,
    ) -> Item:
    """Creates a STAC item for a WorldClim Bioclimatic dataset.

    Args:
        destination (str): Destination directory
        cog_dir_href (str): Directory containing COGs
        cog_href_modifier (ReadHrefModifier, optional): Funtion to apply to the cog_dir_href

    Returns:
        pystac.Item: STAC Item object.
    """
    # item = resolution
    # assets = bioclim variables

    title = 'Worldclim Bioclimatic Variables'
    description = BIOCLIM_DESCRIPTION

    match = re.match(rf".*{WORLDCLIM_VERSION}_(.*)_(.*)_(\d\d).*\.tif",
                     os.path.basename(cog_href))
    if match is None:
        raise ValueError("Could not extract necessary values from {cog_href}")
    res, _, m = match.groups()
    resolution = Resolution(res)

    item = None
    for (data_var, data_var_desc) in BIOCLIM_VARIABLES.items():
        if cog_href_modifier:
            cog_access_href = cog_href_modifier(cog_href)
        else:
            cog_access_href = cog_href

        start_datetime = datetime(
            START_YEAR,
            1,
            tzinfo=timezone.utc,
        )
        end_datetime = datetime(
            END_YEAR,
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
            id = f"wc{WORLDCLIM_VERSION}_{resolution.value}"
            properties = {
                "title":
                f"Worldclim {resolution.value} ",
                "description": BIOCLIM_DESCRIPTION,
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
            item_projection.wkt2 = WORLDCLIM_CRS_WKT
            item_projection.bbox = bbox
            item_projection.transform = transform
            item_projection.shape = shape

        cog_asset = Asset(
            title=data_var,
            description=data_var_desc,
            media_type=MediaType.TIFF,
            roles=["data"],
            href=cog_href,
        )
        item.add_asset(data_var, cog_asset)

        # Include projection information on Asset
        cog_asset_proj = ProjectionExtension.ext(cog_asset,
                                                 add_if_missing=True)
        cog_asset_proj.epsg = item_projection.epsg
        cog_asset_proj.wkt2 = item_projection.wkt2
        cog_asset_proj.transform = item_projection.transform
        cog_asset_proj.bbox = item_projection.bbox
        cog_asset_proj.shape = item_projection.shape

    assert (item is not None)

    # scientific extension
    sci_ext = ScientificExtension.ext(item, add_if_missing=True)
    sci_ext.doi = DOI
    sci_ext.citation = CITATION

    item.set_self_href(
        os.path.join(destination,
                     os.path.basename(cog_href).replace(".tif", ".json")))

    return item

