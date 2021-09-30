import logging
import os
from glob import glob
from subprocess import CalledProcessError, check_output
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve
from zipfile import ZipFile

import rasterio

from stactools.worldclim.constants import (
    DATASET_URL_TEMPLATE,
    MONTHLY_DATA_VARIABLES,
    TILING_PIXEL_SIZE,
)
from stactools.worldclim.enum import Resolution

logger = logging.getLogger(__name__)


def download_convert_dataset(output_path: str) -> None:
    with TemporaryDirectory() as tmp_dir:
        download_dataset(tmp_dir)
        convert_dataset(tmp_dir, output_path)


def download_dataset(output_path: str) -> None:
    for res in Resolution:
        res_path = os.path.join(output_path, res.value)
        os.mkdir(res_path)
        for v in MONTHLY_DATA_VARIABLES.keys():
            var_path = os.path.join(res_path, v)
            os.mkdir(var_path)
            url = DATASET_URL_TEMPLATE.format(resolution=res.value, variable=v)
            # The following shouldn't blow out the memory when loading large files
            with TemporaryDirectory() as tmp_dir:
                tmp_file = os.path.join(tmp_dir, "{res}_{v.value}.zip")
                urlretrieve(url, tmp_file)
                with ZipFile(tmp_file) as zipfile:
                    zipfile.extractall(path=var_path)


def convert_dataset(input_path: str, output_path: str) -> None:
    for file_name in glob(f"{input_path}/**/*.tif", recursive=True):
        if Resolution.THIRTY_SECONDS.value in file_name:
            create_tiled_cogs(file_name, output_path)
        else:
            out_file_name = os.path.join(output_path,
                                         os.path.basename(file_name))
            create_cog(file_name, out_file_name)


def create_tiled_cogs(
    input_file: str,
    output_directory: str,
    raise_on_fail: bool = True,
) -> None:
    """Split tiff into tiles and create COGs

    Args:
        input_path (str): Path to the World Climate data.
        output_directory (str): The directory to which the COG will be written.
        raise_on_fail (bool, optional): Whether to raise error on failure.
            Defaults to True.

    Returns:
        None
    """
    try:
        with TemporaryDirectory() as tmp_dir:
            cmd = [
                "gdal_retile.py",
                "-ps",
                str(TILING_PIXEL_SIZE[0]),
                str(TILING_PIXEL_SIZE[1]),
                "-targetDir",
                tmp_dir,
                input_file,
            ]
            try:
                output = check_output(cmd)
            except CalledProcessError as e:
                output = e.output
                raise
            finally:
                logger.info(f"output: {str(output)}")
            file_names = glob(f"{tmp_dir}/*.tif")
            for f in file_names:
                input_file = os.path.join(tmp_dir, f)
                output_file = os.path.join(
                    output_directory,
                    os.path.basename(f))
                with rasterio.open(input_file, "r") as dataset:
                    contains_data = dataset.read().any()
                # Exclude empty files
                if contains_data:
                    create_cog(input_file, output_file, raise_on_fail, False)

    except Exception:
        logger.error("Failed to process {}".format(input_file))

        if raise_on_fail:
            raise

    return


def create_cog(
    input_path: str,
    output_path: str,
    raise_on_fail: bool = True,
    dry_run: bool = False,
) -> None:
    """Create COG from a tif

    Args:
        input_path (str): Path to World Climate data.
        output_path (str): The path to which the COG will be written.
        raise_on_fail (bool, optional): Whether to raise error on failure.
            Defaults to True.
        dry_run (bool, optional): Run without downloading tif, creating COG,
            and writing COG. Defaults to False.

    Returns:
        None
    """

    output = None
    try:
        if dry_run:
            logger.info(
                "Would have downloaded TIF, created COG, and written COG")
        else:

            cmd = [
                "gdal_translate",
                "-of",
                "COG",
                "-co",
                "NUM_THREADS=ALL_CPUS",
                "-co",
                "BLOCKSIZE=512",
                "-co",
                "COMPRESS=DEFLATE",
                "-co",
                "LEVEL=9",
                "-co",
                "PREDICTOR=YES",
                "-co",
                "OVERVIEWS=IGNORE_EXISTING",
                input_path,
                output_path,
            ]

            try:
                output = check_output(cmd)
            except CalledProcessError as e:
                output = e.output
                raise
            finally:
                logger.info(f"output: {str(output)}")

    except Exception:
        logger.error("Failed to process {}".format(output_path))

        if raise_on_fail:
            raise
