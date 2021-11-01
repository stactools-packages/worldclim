import os.path
from tempfile import TemporaryDirectory

import pystac
# from pystac.stac_io import StacIO
from stactools.testing import CliTestCase

from stactools.worldclim.commands import create_worldclim_command


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self):
        return [create_worldclim_command]

    def test_create_collection(self):
        with TemporaryDirectory() as tmp_dir:
            # Run your custom create-collection command and validate

            # Example:
            destination = tmp_dir

            result = self.run_command(
                ["worldclim", "create-monthly-collection", "-d", destination])

            self.assertEqual(result.exit_code,
                             0,
                             msg="\n{}".format(result.output))

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            collection_file = os.path.join(tmp_dir, "collection.json")
            collection = pystac.read_file(collection_file)
            self.assertEqual(collection.id, "worldclim-monthly")
            # self.assertEqual(item.other_attr...

            collection.validate()

    def test_create_item(self):
        with TemporaryDirectory() as tmp_dir:
            # Run your custom create-item command and validate

            # Example:
            destination = tmp_dir
            result = self.run_command([
                "worldclim",
                "create-monthly-item",
                "-c",
                "tests/data-files/wc2.1_10m_prec_01.tif",
                "-d",
                destination,
            ])
            print(destination)
            self.assertEqual(result.exit_code,
                             0,
                             msg="\n{}".format(result.output))

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            item_file = os.path.join(tmp_dir, "wc2.1_10m_prec_01.json")
            item = pystac.read_file(item_file)
            self.assertEqual(item.id,
                             "wc2.1_10m_1")  # not sure if this is the item ID
            # self.assertEqual(item.other_attr...

            item.validate()
