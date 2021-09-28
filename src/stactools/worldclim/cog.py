import logging

from subprocess import CalledProcessError, check_output

import os
import requests

from io import BytesIO
from glob import glob
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from stactools.worldclim.constants import MONTHLY_DATA_VARIABLES, DATASET_URL_TEMPLATE
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
            response = requests.get(url)
            zipfile = ZipFile(BytesIO(response.content))
            zipfile.extractall(path=var_path)


def convert_dataset(input_path: str, output_path: str) -> None:
    for file_name in glob(f"{input_path}/**/*.tif", recursive=True):
        out_file_name = os.path.join(output_path, os.path.basename(file_name))
        create_cog(file_name, out_file_name)


def create_cog(
    input_path: str,
    output_path: str,
    raise_on_fail: bool = True,
    dry_run: bool = False,
) -> str:
    """Create COG from a tif

    Args:
        input_path (str): Path to World Climate data.
        output_path (str): The path to which the COG will be written.
        raise_on_fail (bool, optional): Whether to raise error on failure.
            Defaults to True.
        dry_run (bool, optional): Run without downloading tif, creating COG,
            and writing COG. Defaults to False.

    Returns:
        str: The path to the output COG.
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

    return output_path
