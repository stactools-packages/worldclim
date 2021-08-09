from datetime import datetime
from stactools_aster.stactools.aster import constants
from stactools.worldclim import constants
from dateutil.relativedelta import relativedelta
import pytz
import json
import logging
from stactools.worldclim import constants
from stactools.worldclim.constants import (WORLDCLIM_ID, WORLDCLIM_EPSG,
                                           WORLDCLIM_TITLE, DESCRIPTION,
                                           WORLDCLIM_PROVIDER, LICENSE,
                                           LICENSE_LINK)

import pystac
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)


def create_item(metadata: dict,
                metadata_url: str,
                cog_href: str = None) -> pystac.Item:
    """Creates a STAC item for a WorldClim dataset.

    Args:
        metadata_url (str): Path to provider metadata.
        cog_href (str, optional): Path to COG asset.

    Returns:
        pystac.Item: STAC Item object.
    """

    title = constants.get("tiff_metadata").get(
        "dct:title")  # reference constants page constants.get
    description = constants.get("description_metadata").get("dct:description")

    utc = pytz.utc

    year = title.split(" ")[0]
    dataset_datetime = utc.localize(datetime.strptime(year, "%Y"))  # not sure

    end_datetime = dataset_datetime + relativedelta(years=5)  # can use months?

    start_datetime = dataset_datetime
    end_datetime = end_datetime

    id = title.replace(" ", "-")
    geometry = json.loads(
        constants.get("geojson_geom").get("@value"))  # files are in tif format
    bbox = Polygon(geometry.get("coordinates")[0]).bounds
    properties = {
        "title": title,
        "description": description,
    }

    # Create item
    item = pystac.Item(
        id=id,
        geometry=geometry,
        bbox=bbox,
        datetime=dataset_datetime,
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
        "metadata",
        pystac.Asset(
            href=metadata_url,
            media_type=pystac.MediaType.JSON,
            roles=["metadata"],
            title="WorldClim version 2.1 metadata",
        ),
    )

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

    return item


def create_collection(metadata: dict):
    # Creates a STAC collection for a WorldClim dataset

    title = metadata.get("tiff_metadata").get("dct:title")

    utc = pytz.utc
    year = title.split(" ")[0]
    dataset_datetime = utc.localize(datetime.strptime(
        year, "%Y"))  # need this to be month

    end_datetime = dataset_datetime + relativedelta(years=5)  # months 01-12

    start_datetime = dataset_datetime
    end_datetime = end_datetime

    geometry = json.loads(metadata.get("geojson_geom").get("@value"))
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
    )
    collection.add_link(LICENSE_LINK)

    return collection
