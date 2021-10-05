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
                            description=BIOCLIM_DESCRIPTION,
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
        for (var_name, var_desc) in BIOCLIM_VARIABLES.items()
    }

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

    # example filename: wc2.1_30s_bio_9.tif

    match = re.match(rf".*{WORLDCLIM_VERSION}_(.*)_(bio_\d+).*\.tif", # rf".*{WORLDCLIM_VERSION}_(.*)_(.*)_(\d\d).*\.tif",
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
            id = f"wc{WORLDCLIM_VERSION}_{resolution.value}_"
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

