import logging
import os
from glob import glob

import click

from stactools.worldclim import cog, stac

logger = logging.getLogger(__name__)


def create_worldclim_command(cli):
    """Creates the stactools-worldclim command line utility."""
    @cli.group(
        "worldclim",
        short_help=("Commands for working with stactools-worldclim"),
    )
    def worldclim():
        pass

    @worldclim.command("create-all-cogs",
                       short_help="Download and convert all data files to COGs"
                       )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    def create_all_cogs(destination: str):
        """Creates a STAC Item
        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Collection
        """

        cog.download_convert_dataset(destination)

    @worldclim.command(
        "create-monthly-collection",
        short_help="Creates a monthly STAC collection",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    def create_collection_command(destination: str):
        """Creates a STAC Collection
        Args:
            destination (str): An HREF for the Collection JSON
        """
        collection = stac.create_monthly_collection()

        collection.set_self_href(os.path.join(destination, "collection.json"))
        collection.normalize_hrefs(destination)
        collection.save_object()
        collection.validate()

        return None

    @worldclim.command(
        "create-monthly-item",
        short_help="Create a monthly STAC item",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    @click.option(
        "-c",
        "--cog",
        required=True,
        help="Location of a directory contining the cogs",
    )
    def create_item_command(destination: str, cog: str):
        """Creates a STAC Item
        Args:
            destination (str): An HREF for the STAC Collection
            cog (str): HREF to the Asset COG
        """
        item = stac.create_monthly_item(destination, cog)
        item.save_object()
        item.validate()

        return None

    @worldclim.command(
        "create-bioclim-item",
        short_help="Create a Bioclimatic STAC item",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    @click.option(
        "-c",
        "--cog",
        required=True,
        help="Location of a directory contining the cogs",
    )
    def create_item_command(destination: str, cog: str):
        """Creates a STAC Item
        Args:
            destination (str): An HREF for the STAC Collection
            cog (str): HREF to the Asset COG
        """
        item = stac.create_bioclim_item(destination, cog)
        item.save_object()
        item.validate()

        return None

    @worldclim.command(
        "create-full-collection",
        short_help="Get all data files and create Items and Collection")
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    def create_full_collection(destination: str):
        """Creates a STAC Collection and all of its Items and Assets
        Args:
            destination (str): An HREF for the STAC Collection
        """

        cog.download_convert_dataset(destination)
        for file_name in glob(f"{destination}/*.tif"):
            print(file_name)
            item = stac.create_monthly_item(destination, file_name)
            print(item.self_href)
            item.save_object()
            item.validate()
        collection = stac.create_monthly_collection()
        collection.set_self_href(os.path.join(destination, "collection.json"))
        collection.normalize_hrefs(destination)
        collection.save_object()
        collection.validate()

    return worldclim


int()
