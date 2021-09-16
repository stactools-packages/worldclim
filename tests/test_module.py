import unittest

import stactools.worldclim


class TestModule(unittest.TestCase):
    def test_version(self):
        self.assertIsNotNone(stactools.worldclim.__version__)


# run other tests here
