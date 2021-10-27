import os.path
from tempfile import TemporaryDirectory

import pystac
from stactools.testing import CliTestCase

from stactools.worldclim.commands import create_worldclim_command


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self):
        return [create_worldclim_command]

    def test_create_collection(self):
        with TemporaryDirectory() as tmp_dir:
            # Run your custom create-collection command and validate

            # Example:
            destination = os.path.join(tmp_dir, "collection.json")

            result = self.run_command(
                ["worldclim", "create-monthly-collection", "-d", destination])

            self.assertEqual(result.exit_code,
                             0,
                             msg="\n{}".format(result.output))

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            collection = pystac.read_file(destination)
            self.assertEqual(collection.id, "worldclim-monthly")
            # self.assertEqual(item.other_attr...

            collection.validate()

    def test_create_item(self):
        with TemporaryDirectory() as tmp_dir:
            # Run your custom create-item command and validate

            # Example:
            destination = os.path.join(tmp_dir, "collection.json")
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

            item = pystac.read_file(destination)
            self.assertEqual(item.id, "prec") # not sure if this is the item ID
            # self.assertEqual(item.other_attr...

            item.validate()
