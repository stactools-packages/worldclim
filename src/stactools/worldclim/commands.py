import click
import logging
import os

from stactools.worldclim import stac

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

    @worldclim.command("create-monthly-item",
                       short_help="Create a monthly STAC item")
    @click.argument("destination")
    @click.argument("resolution_href")
    @click.argument("month_href")
    @click.argument("directory_loc")

    def create_item_command(destination: str,
                        resolution_href: str,
                        month_href: str,
                        directory_loc: os.path):

        """Creates a STAC Item
        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Collection
        """

        item = stac.create_monthly_item(resolution_href, month_href, directory_loc)
        item.set_self_href(destination)
        item.save_object()

        return None

    return worldclim
