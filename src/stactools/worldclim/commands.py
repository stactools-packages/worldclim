import logging
import os
import shutil
from glob import glob

import click

from stactools.worldclim import cog, stac
from stactools.worldclim.constants import MONTHLY_DATA_VARIABLES

logger = logging.getLogger(__name__)


def create_worldclim_command(cli):
    """Creates the stactools-worldclim command line utility."""
    @cli.group(
        "worldclim",
        short_help=("Commands for working with stactools-worldclim"),
    )
    def worldclim():
        pass

    @worldclim.command(
        "create-all-monthly-cogs",
        short_help="Download and convert all data files to COGs",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    def create_all_monthly_cogs(destination: str):
        """Creates a STAC Item
        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Collection
        """

        cog.download_convert_monthly_dataset(destination)

    @worldclim.command(
        "create-all-bioclim-cogs",
        short_help="Download and convert all data files to COGs",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    def create_all_bioclim_cogs(destination: str):
        """Creates a STAC Item
        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Collection
        """

        cog.download_convert_bioclim_dataset(destination)

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
        "create-monthly-collection",
        short_help="Creates a monthly STAC collection",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    def create_monthly_collection_command(destination: str):
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
        "create-bioclim-collection",
        short_help="Creates a monthly STAC collection",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    def create_bioclim_collection_command(destination: str):
        """Creates a STAC Collection
        Args:
            destination (str): An HREF for the Collection JSON
        """
        collection = stac.create_bioclim_collection()

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
    def create_monthly_item_command(destination: str, cog: str):
        """Creates a STAC Item
        Args:
            destination (str): Output directory
            cog (str): HREF to the Asset COG
        """

        item = stac.create_monthly_item(cog)
        item.save_object(dest_href=os.path.join(
            destination,
            os.path.basename(cog).replace(".tif", ".json")))
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
    def create_bioclim_item_command(destination: str, cog: str):
        """Creates a STAC Item
        Args:
            destination (str): An HREF for the STAC Collection
            cog (str): HREF to the Asset COG
        """
        item = stac.create_bioclim_item(cog)
        item.save_object(dest_href=os.path.join(
            destination,
            os.path.basename(cog).replace(".tif", ".json")))
        item.save_object()
        item.validate()

        return None

    @worldclim.command(
        "create-full-monthly-collection",
        short_help="Get all data files and create Items and Collection",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    def create_full_monthly__collection(destination: str):
        """Creates a STAC Collection and all of its Items and Assets
        Args:
            destination (str): An HREF for the STAC Collection
        """
        os.chdir(destination)
        collection = stac.create_monthly_collection()
        collection.normalize_hrefs("./")
        collection.save(dest_href="./")
        cog.download_convert_monthly_dataset("./")
        for file_name in glob("./*tmin*.tif"):
            logger.info(f"Processing {file_name}")
            id = stac.create_monthly_item(file_name).id
            os.makedirs(id, exist_ok=True)
            for data_var in MONTHLY_DATA_VARIABLES.keys():
                var_file_name = file_name.replace("tmin", data_var)
                shutil.move(var_file_name, os.path.join(id, var_file_name))
            item = stac.create_monthly_item(os.path.join(id, file_name))
            collection.add_item(item)
            item.validate()
        logger.info("Saving collection")
        collection.normalize_hrefs("./")
        collection.make_all_asset_hrefs_relative()
        collection.save(dest_href="./")
        collection.validate()

    @worldclim.command(
        "create-full-bioclim-collection",
        short_help="Get all data files and create Items and Collection",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    def create_full_bioclim__collection(destination: str):
        """Creates a STAC Collection and all of its Items and Assets
        Args:
            destination (str): An HREF for the STAC Collection
        """
        os.chdir(destination)
        collection = stac.create_bioclim_collection()
        collection.normalize_hrefs("./")
        collection.save(dest_href="./")
        cog.download_convert_bioclim_dataset("./")
        for file_name in glob("./*.tif"):
            logger.info(f"Processing {file_name}")
            id = os.path.basename(file_name).replace(".tif", "")
            item_dir = id
            os.makedirs(item_dir, exist_ok=True)
            new_file_name = os.path.join(item_dir, f"{id}.tif")
            shutil.move(file_name, new_file_name)
            item = stac.create_bioclim_item(new_file_name)
            collection.add_item(item)
            item.validate()
        logger.info("Saving collection")
        collection.normalize_hrefs("./")
        collection.make_all_asset_hrefs_relative()
        collection.save(dest_href="./")
        collection.validate()

    return worldclim
