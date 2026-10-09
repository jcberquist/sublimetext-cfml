# This module parses the source of a component file into its metadata: the
# attributes of the component, its properties and its functions. The shape of
# the metadata is described in the metadata module.


from typing import Any, cast
from . import cfml_functions, cfml_properties, regex, ranges
from .metadata import ComponentMetadata, Function, Property


def parse_cfc_file_string(file_string) -> ComponentMetadata:
    cfscript_range = ranges.RangeWalker(file_string, 0, 'cfscript').walk()
    cfc_index: dict[str, Any] = {}

    tag_text = ranges.TagText(file_string)
    component_search = find_component(file_string, cfscript_range, tag_text)

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

    # in a script component a tag is text, as in the strings of code that
    # writes a component, so there the strings and comments of script hide it
    hidden_tags = tag_text
    if component_search and not component_search.group(2).startswith('<'):
        hidden_tags = ranges.ScriptText(cfscript_range)

    properties = cfml_properties.index(file_string, cfscript_range, hidden_tags)
    functions = cfml_functions.index(file_string, cfscript_range, hidden_tags)

    cfc_index["properties"] = prop_metadata_dict(properties)
    cfc_index["functions"] = get_accessors_metadata_dict(cfc_index["accessors"] or cfc_index["persistent"], properties)
    cfc_index["functions"].update(funct_metadata_dict(functions))

    return cast(ComponentMetadata, cfc_index)


def find_component(file_string, cfscript_range, tag_text):
    # the word component in a comment or string above the declaration is
    # not the declaration
    pos = 0
    while True:
        component_search = regex.component.search(file_string, pos)
        if component_search is None:
            return None
        keyword_pt = component_search.start(2)
        if component_search.group(2).startswith('<'):
            hidden = tag_text.contains(keyword_pt)
        else:
            hidden = cfscript_range.is_in_range(keyword_pt, ranges.NON_SCRIPT_RANGES)
        if not hidden:
            return component_search
        # a match runs on to the next `{`, past the declaration
        pos = component_search.end(2)


def funct_metadata_dict(functions) -> dict[str, Function]:
    meta = {}
    for function_name in functions:
        meta[function_name.lower()] = {
            "name": function_name,
            "meta": functions[function_name],
            "implicit": False
        }
    return meta


def prop_metadata_dict(properties) -> dict[str, Property]:
    meta = {}
    for prop_name in properties:
        meta[prop_name.lower()] = {
            "name": prop_name,
            "meta": properties[prop_name]
        }
    return meta


def get_accessors_metadata_dict(cfc_accessors, properties) -> dict[str, Function]:
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
            arg: dict[str, Any] = {"default": None}
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
