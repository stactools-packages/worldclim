import stactools.core

from stactools.worldclim.stac import create_monthly_item
from stactools.worldclim.cog import create_cog

stactools.core.use_fsspec()


def register_plugin(registry):
    from stactools.worldclim import commands
    registry.register_subcommand(commands.create_worldclim_command)


__all__ = [create_cog, create_monthly_item]

__version__ = '0.1.0'
