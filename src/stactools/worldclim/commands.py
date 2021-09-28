import click
import logging

from stactools.worldclim import cog, stac
from stactools.worldclim.enum import Month, Resolution

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
    @click.argument("destination")
    def create_collection_command(destination: str):
        """Creates a STAC Collection
        Args:
            destination (str): An HREF for the Collection JSON
        """
        collection = stac.create_monthly_collection()

        collection.set_self_href(destination)

        collection.save_object()

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
        "-r",
        "--resolution",
        required=True,
        help="Resolution of the data",
    )
    @click.option(
        "-m",
        "--month",
        required=True,
        help="Month of the data",
    )
    @click.option(
        "-c",
        "--cogs",
        required=True,
        help="Location of a directory contining the cogs",
    )
    def create_item_command(destination: str, resolution: str, month: str,
                            cogs: str):
        """Creates a STAC Item
        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Collection
        """
        item = stac.create_monthly_item(Resolution(resolution),
                                        Month(int(month)), destination, cogs)
        item.save_object()
        item.validate()

        return None

    return worldclim


int()
