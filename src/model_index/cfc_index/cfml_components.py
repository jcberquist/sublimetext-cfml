# This module, via index(), takes in a directory path and recursively
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

# currently trying out threading the cfc regex parsing as per:
# http://www.toptal.com/python/beginners-guide-to-concurrency-and-parallelism-in-python
# In my testing most time in the index function is spent walking the file
# system and reading files - so this is a test to see if offloading file string
# parsing to threads will allow file I/O wait time to be used for parsing and
# reduce the overall indexing time.

import os
import re
from collections import namedtuple
from queue import Queue
from threading import Thread
from . import cfml_functions, cfml_properties, regex

FunctionTuple = namedtuple("FunctionTuple", "name meta implicit")
PropertyTuple = namedtuple("PropertyTuple", "name meta")


class RegExWorker(Thread):
    def __init__(self, index_queue, cfcs):
        Thread.__init__(self)
        self.index_queue = index_queue
        self.cfcs = cfcs

    def run(self):
        while True:
            full_file_path, file_string = self.index_queue.get()
            self.cfcs[full_file_path] = parse_cfc_file_string(file_string)
            self.index_queue.task_done()


def index(root_path):
    cfcs = {}

    index_queue = Queue()
    for x in range(4):
        regex_worker = RegExWorker(index_queue, cfcs)
        regex_worker.daemon = True
        regex_worker.start()

    for path, directories, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.endswith(".cfc"):
                full_file_path = path.replace("\\", "/") + "/" + filename
                try:
                    with open(full_file_path, "r", encoding="utf-8") as f:
                        file_string = f.read()
                except:
                    print("CFML: unable to read file - " + full_file_path)
                else:
                    index_queue.put((full_file_path, file_string))

    index_queue.join()
    return cfcs


def index_file(full_file_path):
    try:
        with open(full_file_path, "r", encoding="utf-8") as f:
            file_string = f.read()
    except:
        print("CFML: unable to read file - " + full_file_path)
        return {}
    return parse_cfc_file_string(file_string)


def parse_cfc_file_string(file_string):
    cfc_index = {}

    component_search = re.search(regex.component, file_string)

    if component_search:
        component = regex.Component._make(component_search.groups())

        if component.docblock:
            docblock = cfml_functions.parse_docblock(component.docblock)
            for key in docblock:
                d = docblock[key]
                full_key = d.key.lower() + '.' + d.subkey.lower() if len(d.subkey) > 0 else d.key.lower()
                cfc_index[full_key] = d.value

        cfc_index.update(cfml_functions.parse_attributes(component.attributes))

    for key in ["extends", "initmethod", "entityname"]:
        if key not in cfc_index:
            cfc_index[key] = None

    for key in ["accessors", "persistent"]:
        if key in cfc_index and cfc_index[key].lower() in ["true", "yes"]:
            cfc_index[key] = True
        else:
            cfc_index[key] = False

    properties = cfml_properties.index(file_string)
    functions = cfml_functions.index(file_string)

    cfc_index["properties"] = prop_metadata_dict(properties)
    cfc_index["functions"] = get_accessors_metadata_dict(cfc_index["accessors"], properties)
    cfc_index["functions"].update(funct_metadata_dict(functions))

    return cfc_index


def funct_metadata_dict(functions):
    return {function_name.lower(): FunctionTuple(function_name, functions[function_name], False) for function_name in functions}


def prop_metadata_dict(properties):
    return {prop_name.lower(): PropertyTuple(prop_name, properties[prop_name]) for prop_name in properties}


def get_accessors_metadata_dict(cfc_accessors, properties):
    """
    build a FunctionTuple for each property that has a getter and/or a setter
    these will be used as a base for explicit functions to be merged into
    """
    meta = {}
    for prop_name in properties:
        attrs = properties[prop_name]
        cased_prop_name = prop_name[0].upper() + prop_name[1:]

        # getter
        if attrs["getter"] or (attrs["getter"] is None and cfc_accessors):
            funct_meta = {"access": "public", "arguments": []}
            funct_meta["returntype"] = attrs["type"]
            meta["get" + prop_name.lower()] = FunctionTuple("get" + cased_prop_name, funct_meta, True)

        # setter
        if attrs["setter"] or (attrs["setter"] is None and cfc_accessors):
            funct_meta = {"access": "public", "arguments": []}
            arg = {"default": None}
            arg["name"] = prop_name
            arg["required"] = True
            arg["type"] = attrs["type"]
            funct_meta["returntype"] = "void"
            funct_meta["arguments"].append(arg)
            meta["set" + prop_name.lower()] = FunctionTuple("set" + cased_prop_name, funct_meta, True)

    return meta
