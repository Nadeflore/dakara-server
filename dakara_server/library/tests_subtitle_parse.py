import os
from django.test import TestCase
from .management.commands.feed import ASSParser

RESSOURCES_DIR = os.path.join("tests_ressources", "subtitles")
APP_DIR = os.path.dirname(os.path.abspath(__file__))


class ASSParserTestCase(TestCase):

    def test_subtitles_from_files(self):
        """
        For each subtitle file in ressource directory,
        open and extract lyrics from the file,
        and test that the result is the same
        as the corresponding file with "_expected" prefix

        This method is called from tests methods
        """
        directory = os.path.join(APP_DIR, RESSOURCES_DIR)
        for file_name in os.listdir(directory):
            if not file_name.endswith("_expected"):

                file_path = os.path.join(directory, file_name)

                parser = ASSParser(file_path)
                lyrics = parser.get_lyrics()

                # Check against expected file

                with open(file_path + "_expected") as expected:
                    lines = lyrics.splitlines()
                    expected_lines = expected.read().splitlines()

                    self.assertEqual(lines, expected_lines, "In file: {}".format(file_name))
