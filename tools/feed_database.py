#!/usr/bin/env python3
##
# Dakara Project
#
# Script for feeding the server database with songs from a directory
#

import os
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dakara_server.settings")
sys.path.append("../dakara_server/")

try:
    from library.models import Song
except ImportError as e:
    print("Unable to import Django modules:\n" + str(e))

file_coding = sys.getfilesystemencoding()


class FeedDatabase:
    """ Class representing a list of files to feed the database with
    """

    def __init__(self, listing, prefix="", test=False):
        """ Constructor

            input:
                listing <list> list of file names
                prefix <str> directory prefix to be appended to file name
                test <bool> flag for test (no save in database) mode
        """
        self.listing_raw = listing
        self.prefix = prefix
        self.test = test
        self.listing = []

    @classmethod
    def from_directory(cls, directory_path, *args, **kwargs):
        """ Overloaded constructor
            Extract files from directory

            input:
                directory_path <str> path of directory to extract songs

            output:
                <object> FeedDatabase object
        """
        directory_path_encoded = directory_path.encode(file_coding)
        listing = []
        for file in os.listdir(directory_path_encoded):
            file_decoded = file.decode(file_coding)
            if os.path.isfile(os.path.join(directory_path_encoded, file)) and \
                    os.path.splitext(file_decoded)[1] not in ('.ssa', '.ass', '.srt', '.db') and \
                    file_decoded[0] != ".":
                listing.append(file_decoded)
        return cls(listing, *args, **kwargs)

    def extract_attributes(self):
        """ Extract database fields from files
        """

        listing = []
        for file in self.listing_raw:
            title = os.path.splitext(file)[0]
            listing.append((title, file))
        self.listing = listing

    def save(self):
        """ Save list in database
        """
        for title, file in self.listing:
            file_path = os.path.join(self.prefix, file)
            song = Song(
                    title=title,
                    file_path=file_path
                    )
            if not self.test:
                print("Saving: " + title)
                song.save()
            else:
                print("To save:\n" + title + "\n" + file_path)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
            description="Import songs from files and feed the Django database with it"
            )
    parser.add_argument(
            "directory",
            help="path of the directory to scan"
            )
    parser.add_argument(
            "-p",
            "--prefix",
            help="prefix to add to file path stored in database"
            )
    parser.add_argument(
            "-t",
            "--test-mode",
            help="run script in test mode, don't save anything in database",
            action="store_true"
            )

    args = parser.parse_args()

    feed_database = FeedDatabase.from_directory(
            directory_path=args.directory,
            prefix=args.prefix or "",
            test=args.test_mode

            )
    feed_database.extract_attributes()
    feed_database.save()

