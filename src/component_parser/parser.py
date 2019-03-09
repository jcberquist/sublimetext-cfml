# This module takes in a directory path and recursively
# browses it and its subfolders looking for ".cfc" files, and then uses the
# cfml_functions module to index the functions from those files.
# It assumes that all such files in the directory are component files, and does
# not check that the files actually define components. It returns a dict of
# normalized file paths mapped to a named tuple containing function metadata
# and completions.

# The returned dict structure looks like this:
# {
#   "/path/to/mycfc.cfc": {
#     "accessors": true/false,
#     "entityname": entityname,
#     "extends": extends,
#     "functions": metadata,
#     "initmethod": initmethod,
#     "persistent": true/false,
#     "properties": metadata
#   },
#   ...
# }


import os
import traceback
import sqlite3
import json
import hashlib

from queue import Queue
from threading import Thread
from time import sleep
from . import cfml_components


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


CLEAR_PATHS = """
DELETE FROM file_hashes
WHERE file_path IN(?);
"""


class RegExWorker(Thread):
    def __init__(self, parse_queue, cfcs, cache_path=None):
        Thread.__init__(self)
        self.parse_queue = parse_queue
        self.cfcs = cfcs
        self.cache_path = cache_path

    def run(self):
        con = sqlite3.connect(self.cache_path) if self.cache_path else None

        while True:
            full_file_path, file_hash, file_string = self.parse_queue.get()
            if full_file_path is None:
                break
            try:
                self.cfcs[full_file_path] = cfml_components.parse_cfc_file_string(
                    file_string
                )
                if con:
                    metadata = json.dumps(self.cfcs[full_file_path])
                    con.execute(UPSERT_METADATA, (file_hash, metadata))
                    con.execute(UPSERT_FILE_PATH, (full_file_path, file_hash))
            except Exception:
                print("CFML: unable to parse file - " + full_file_path)
                traceback.print_exc()
            self.parse_queue.task_done()
            sleep(0.01)

        if con:
            con.commit()
            con.close()


class Parser:
    def __init__(self, cache_path=None):
        self.cache_path = cache_path
        self.init_cache()
        self.clean_cache()

    def init_cache(self):
        if self.cache_path:
            con = sqlite3.connect(self.cache_path)
            con.executescript(CREATE_CACHE_TABLES)
            con.commit()
            con.close()

    def clean_cache(self):
        if not self.cache_path:
            return

        con = sqlite3.connect(self.cache_path)

        invalid_paths = []
        for file_path, file_hash in con.execute(SELECT_FILE_HASHES):
            if not os.path.isfile(file_path):
                invalid_paths.append(file_path)

        if len(invalid_paths) > 0:
            con.execute(CLEAR_PATHS, (",".join(invalid_paths),))

        con.execute(CLEAN_CACHE)

        con.commit()
        con.close()

    def flush_cache(self):
        pass

    def parse_directory(self, root_path):
        cfcs = {}
        cache = {}

        parse_queue = Queue()
        regex_worker = RegExWorker(parse_queue, cfcs, self.cache_path)
        regex_worker.start()

        if self.cache_path:
            con = sqlite3.connect(self.cache_path)
            for file_hash, metadata in con.execute(SELECT_METADATA):
                cache[file_hash] = metadata
            con.close()

        for path, directories, filenames in os.walk(root_path):
            for filename in filenames:

                if filename.endswith(".cfc"):
                    full_file_path = path.replace("\\", "/") + "/" + filename

                    try:
                        with open(full_file_path, "r", encoding="utf-8") as f:
                            file_string = f.read()
                    except Exception:
                        print("CFML: unable to read file - " + full_file_path)
                    else:
                        file_hash = hashlib.md5(file_string.encode("utf-8")).hexdigest()

                        if file_hash in cache:
                            cfcs[full_file_path] = json.loads(cache[file_hash])
                            continue

                        parse_queue.put((full_file_path, file_hash, file_string))

        parse_queue.join()
        parse_queue.put((None, None, None))
        regex_worker.join()

        return cfcs

    def parse_file(self, full_file_path):
        con = sqlite3.connect(self.cache_path) if self.cache_path else None

        try:
            with open(full_file_path, "r", encoding="utf-8") as f:
                file_string = f.read()
        except Exception:
            print("CFML: unable to read file - " + full_file_path)
            return {}

        file_hash = hashlib.md5(file_string.encode("utf-8")).hexdigest()

        if con:
            s = con.execute(SEARCH_HASH_METADATA, (file_hash,)).fetchone()
            if s:
                con.execute(UPSERT_FILE_PATH, (full_file_path, file_hash))
                con.commit()
                con.close()
                return json.loads(s[1])

        metadata = cfml_components.parse_cfc_file_string(file_string)

        if con:
            con.execute(UPSERT_METADATA, (file_hash, json.dumps(metadata)))
            con.execute(UPSERT_FILE_PATH, (full_file_path, file_hash))
            con.commit()
            con.close()

        return metadata
