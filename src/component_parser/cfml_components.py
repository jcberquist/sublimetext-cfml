# This module, via index(), takes in a directory path and recursively
# browses it and its subfolders looking for ".cfc" files, and then uses the
# functions module to index the functions from those files.
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


import re
from . import cfml_functions, cfml_properties, regex, ranges


def parse_cfc_file_string(file_string):
    cfscript_range = ranges.RangeWalker(file_string, 0, 'cfscript').walk()
    cfc_index = {}

    component_search = re.search(regex.component, file_string)

    if component_search:
        component = regex.Component(
            component_search.group(2).startswith('component'), 
            component_search.group(1), 
            component_search.group(3)
        )

        if component.docblock:
            docblock = cfml_functions.parse_docblock(component.docblock)
            for key in docblock:
                for d in docblock[key]:
                    full_key = d.key.lower() + '.' + d.subkey.lower() if len(d.subkey) > 0 else d.key.lower()
                    cfc_index[full_key] = d.value.strip()

        cfc_index.update(cfml_functions.parse_attributes(component.attributes))

    for key in ["extends", "initmethod", "entityname"]:
        if key not in cfc_index:
            cfc_index[key] = None

    for key in ["accessors", "persistent"]:
        if key in cfc_index and cfc_index[key].lower() in ["true", "yes"]:
            cfc_index[key] = True
        else:
            cfc_index[key] = False

    properties = cfml_properties.index(file_string, cfscript_range)
    functions = cfml_functions.index(file_string, cfscript_range)

    cfc_index["properties"] = prop_metadata_dict(properties)
    cfc_index["functions"] = get_accessors_metadata_dict(cfc_index["accessors"] or cfc_index["persistent"], properties)
    cfc_index["functions"].update(funct_metadata_dict(functions))

    return cfc_index


def funct_metadata_dict(functions):
    meta = {}
    for function_name in functions:
        meta[function_name.lower()] = {
            "name": function_name,
            "meta": functions[function_name],
            "implicit": False
        }
    return meta


def prop_metadata_dict(properties):
    meta = {}
    for prop_name in properties:
        meta[prop_name.lower()] = {
            "name": prop_name,
            "meta": properties[prop_name]
        }
    return meta


def get_accessors_metadata_dict(cfc_accessors, properties):
    """
    build a dict for each property that has a getter and/or a setter
    these will be used as a base for explicit functions to be merged into
    """
    meta = {}
    for prop_name in properties:
        attrs = properties[prop_name]
        cased_prop_name = prop_name[0].upper() + prop_name[1:]

        # getter
        if attrs["getter"] or (attrs["getter"] is None and cfc_accessors):
            funct_meta = {"access": "public", "parameters": []}
            funct_meta["returntype"] = attrs["type"]
            meta["get" + prop_name.lower()] = {
                "name": "get" + cased_prop_name,
                "meta": funct_meta,
                "implicit": True
            }

        # setter
        if attrs["setter"] or (attrs["setter"] is None and cfc_accessors):
            funct_meta = {"access": "public", "parameters": []}
            arg = {"default": None}
            arg["name"] = prop_name
            arg["required"] = True
            arg["type"] = attrs["type"]
            funct_meta["returntype"] = "void"
            funct_meta["parameters"].append(arg)
            meta["set" + prop_name.lower()] = {
                "name": "set" + cased_prop_name,
                "meta": funct_meta,
                "implicit": True
            }

    return meta
