# This module finds the ".cfc" files in a directory and its subfolders, or
# takes a list of them, and parses each into its metadata with the
# cfml_components module, keeping the metadata of files it has parsed before
# in a cache. It assumes that all such files are component files, and does
# not check that they define components.


import hashlib
import json
import os
import sqlite3
import traceback
from contextlib import closing
from . import cfml_components
from .metadata import ComponentMetadata


CREATE_CACHE_TABLES = """
CREATE TABLE IF NOT EXISTS file_hashes (
    file_path TEXT PRIMARY KEY ASC,
    hash TEXT
);
CREATE TABLE IF NOT EXISTS hash_metadata (
    hash TEXT PRIMARY KEY ASC,
    metadata TEXT
);
"""


SELECT_FILE_HASHES = """
SELECT file_path, hash
FROM file_hashes
"""


SELECT_METADATA = """
SELECT hash, metadata
FROM hash_metadata
"""


SEARCH_HASH_METADATA = """
SELECT hash, metadata
FROM hash_metadata
WHERE hash = ?;
"""


UPSERT_FILE_PATH = """
INSERT OR REPLACE INTO file_hashes (file_path, hash)
VALUES (?, ?);
"""


UPSERT_METADATA = """
INSERT OR REPLACE INTO hash_metadata (hash, metadata)
VALUES (?, ?);
"""


CLEAN_CACHE = """
DELETE FROM hash_metadata
WHERE hash NOT IN (
    SELECT hash FROM file_hashes
);
"""


CLEAR_PATH = """
DELETE FROM file_hashes
WHERE file_path = ?;
"""


CLEAR_CACHE = """
DELETE FROM file_hashes;
DELETE FROM hash_metadata;
"""


class Parser:
    def __init__(self, cache_path):
        self.cache_path = cache_path
        try:
            self.init_cache()
            self.clean_cache()
        except sqlite3.OperationalError:
            # locked, or it cannot be opened: a new file does not help
            raise
        except sqlite3.DatabaseError:
            # not a database, or a damaged one: the cache is derived data,
            # so start it again
            print(
                'CFML: the component index cache was unreadable and is reset - '
                + cache_path
            )
            os.remove(cache_path)
            self.init_cache()

    def connect(self):
        # a connection's own context manager only commits, so close it too
        return closing(sqlite3.connect(self.cache_path))

    def init_cache(self):
        with self.connect() as con, con:
            con.executescript(CREATE_CACHE_TABLES)

    def clean_cache(self):
        with self.connect() as con, con:
            invalid_paths = [
                (file_path,)
                for file_path, file_hash in con.execute(SELECT_FILE_HASHES)
                if not os.path.isfile(file_path)
            ]
            con.executemany(CLEAR_PATH, invalid_paths)
            con.execute(CLEAN_CACHE)

    def clear_cache(self):
        """Empties the cache, so that every file is parsed again."""
        with self.connect() as con, con:
            con.executescript(CLEAR_CACHE)

    def parse_directory(self, root_path) -> dict[str, ComponentMetadata]:
        """Returns the metadata of the component files in a folder, by path."""
        return self.parse_files(find_component_files(root_path))

    def parse_files(self, file_paths) -> dict[str, ComponentMetadata]:
        """
        Returns the metadata of the files, by path, leaving out those that
        cannot be read or parsed.
        """
        cfcs = {}

        with self.connect() as con, con:
            cache = dict(con.execute(SELECT_METADATA))

            for full_file_path in file_paths:
                file_string = read_file(full_file_path)
                if file_string is None:
                    continue
                file_hash = get_hash(file_string)

                if file_hash in cache:
                    metadata = json.loads(cache[file_hash])
                else:
                    try:
                        metadata = cfml_components.parse_cfc_file_string(file_string)
                    except Exception:
                        print('CFML: unable to parse file - ' + full_file_path)
                        traceback.print_exc()
                        continue
                    con.execute(UPSERT_METADATA, (file_hash, json.dumps(metadata)))

                # record the path on a cache hit too, or clean_cache() can
                # drop the metadata this file now uses
                cfcs[full_file_path] = metadata
                con.execute(UPSERT_FILE_PATH, (full_file_path, file_hash))

        return cfcs

    def parse_file(self, full_file_path) -> ComponentMetadata | None:
        """
        Returns the metadata of a file, or None if it cannot be read or
        parsed.
        """
        file_string = read_file(full_file_path)
        if file_string is None:
            return None

        file_hash = get_hash(file_string)

        with self.connect() as con, con:
            cached = con.execute(SEARCH_HASH_METADATA, (file_hash,)).fetchone()
            if cached:
                metadata = json.loads(cached[1])
            else:
                try:
                    metadata = cfml_components.parse_cfc_file_string(file_string)
                except Exception:
                    print('CFML: unable to parse file - ' + full_file_path)
                    traceback.print_exc()
                    return None
                con.execute(UPSERT_METADATA, (file_hash, json.dumps(metadata)))
            con.execute(UPSERT_FILE_PATH, (full_file_path, file_hash))

        return metadata


def is_component_file(file_path):
    return file_path.endswith('.cfc')


def find_component_files(root_path):
    for path, _directories, filenames in os.walk(root_path):
        for filename in filenames:
            if is_component_file(filename):
                yield path.replace('\\', '/') + '/' + filename


def read_file(full_file_path):
    try:
        with open(full_file_path, encoding='utf-8') as f:
            return f.read()
    except OSError, UnicodeDecodeError:
        print('CFML: unable to read file - ' + full_file_path)
        return None


# part of every cache key: change it when the parsed metadata changes, so
# files cached by an older version are parsed again
PARSER_VERSION = '18'


def get_hash(file_string):
    key = PARSER_VERSION + '\n' + file_string
    return hashlib.md5(key.encode('utf-8'), usedforsecurity=False).hexdigest()
