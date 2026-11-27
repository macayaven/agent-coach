import unittest

from app import slugify


class SlugifyTests(unittest.TestCase):
    def test_spaces(self):
        self.assertEqual(slugify("Hello World"), "hello-world")
