import unittest

from stactools.worldclim import stac


class StacTest(unittest.TestCase):
    def test_create_collection(self):
        # Write tests for each for the creation of a STAC Collection
        # Create the STAC Collection...
        collection = stac.create_monthly_collection()
        collection.set_self_href("")

        # Check that it has some required attributes
        self.assertEqual(collection.id, "worldclim-monthly")
        # self.assertEqual(collection.other_attr...

        # Validate
        collection.validate()

    def test_create_item(self):
        # Write tests for each for the creation of STAC Items
        # Create the STAC Item...
        item = stac.create_monthly_item(
            "/Users/cpapalaz/Downloads/wc2.1_2.5m_prec/",
            "/Users/cpapalaz/Downloads/wc2.1_2.5m_prec/wc2.1_2.5m_prec_05.tif"
        )  # change this

        # Check that it has some required attributes
        self.assertEqual(item.id,
                         "wc2.1_2.5m_5")  # create IDs for all other items
        # self.assertEqual(item.other_attr...

        # Validate
        item.validate()
