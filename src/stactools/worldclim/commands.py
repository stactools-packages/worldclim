import click
import logging
import os

from stactools.worldclim import stac
from stactools.worldclim import cog
from stactools.worldclim import constants
from stactools.worldclim.constants import WORLDCLIM_ID

logger = logging.getLogger(__name__)


def create_worldclim_command(cli):
    """Creates the worldclim command line utility."""
    @cli.group(
        "worldclim",
        short_help=(
            "Commands for working with WorldClim Historical Climate data"  # change
        ),
    )
    def worldclim():
        pass

    @worldclim.command(
        "create-catalog",
        short_help="Create a STAC catalog for WorldClim version 2.1 dataset.",
    )
    @click.argument("destination")
    def create_catalog_command(destination: str, source: str):
        """Creates a STAC Catalog from WorldClim constants file

        Args:
            destination (str): Path to output STAC catalog.
            source (str): Path to NRCan provided metadata - Currently only supports JSON-LD. #dont have this for worldclim, source=constants

        Returns:
            Callable
        """

        json_path = source

        metadata = constants.get_metadata(json_path)
        metadata = constants.get_metadata(
            json_path)  # reference constants instead of utils

        asset_package_path = constants.download_asset_package(metadata)

        tif_path = os.path.join(asset_package_path, [
            i for i in os.listdir(asset_package_path) if i.endswith(".tif")
        ][0])

        output_path = destination.replace(".tif", "_cog.tif")

        # Create cog asset
        cog_path = cog.create_cog(tif_path, output_path, dry_run=False)

        # Create stac item
        item = stac.create_item(metadata, json_path, cog_path, destination)
        item.collection_id = WORLDCLIM_ID

        collection = stac.create_collection(metadata)
        collection.add_item(item)
        collection_dir = os.path.dirname(os.path.dirname(destination))

        collection.normalize_hrefs(collection_dir)
        collection.save()
        collection.validate()

    @worldclim.command(
        "create-cog",
        short_help="Transform Geotiff to Cloud-Optimized Geotiff.",
    )
    @click.option("--output",
                  required=True,
                  help="The output directory to write the COGs to.")
    def create_cogs(path_to_cogs: str):
        # Fill this in
        return False

    return worldclim
