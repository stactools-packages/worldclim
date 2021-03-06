import stactools.core

from stactools.worldclim.cog import create_cog
from stactools.worldclim.stac import create_monthly_item

stactools.core.use_fsspec()


def register_plugin(registry):
    from stactools.worldclim import commands
    registry.register_subcommand(commands.create_worldclim_command)


__all__ = [create_cog.__name__, create_monthly_item.__name__]

__version__ = '0.1.5'
"""Library version"""
