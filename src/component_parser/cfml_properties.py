# This module, via index(), takes in a cfml source file string and
# returns a python dict of the property names mapped to a dict
# containing data about the property.

# The structure looks like this:
# {
#   "property_name": {
#     "type": "any/string/numeric/etc",
#     "getter": True/False/None
#     "setter": True/False/None
#   },
#   ...
# }

import re
from . import cfml_functions, regex, ranges



def index(file_string, cfscript_range=None):
    if cfscript_range is None:
        cfscript_range = ranges.RangeWalker(file_string, 0, 'cfscript').walk()

    properties = {}
    for property_match in re.finditer(regex.cfml_property, file_string):

        if cfscript_range.is_in_range(property_match.start(), ranges.NON_SCRIPT_RANGES):
            continue

        property_string = property_match.group()

        if not property_string.startswith('<cf'):
            dr = cfscript_range.deepest_range(property_match.start())
            if dr.depth() != 2:
                continue

        property_string = property_match.group(1)

        # search for 'property type name;' syntax
        type_name_search = re.search(regex.property_type_name, property_string)
        if type_name_search:
            property_string = property_string.replace(type_name_search.group(0), "")

        attributes = find_property_attributes(property_string)

        if type_name_search:
            attributes["name"] = type_name_search.group(2)
        if type_name_search and type_name_search.group(1):
            attributes["type"] = type_name_search.group(1)

        if "name" in attributes:
            property_name = attributes["name"]
            del attributes["name"]
            properties[property_name] = attributes
    return properties


def find_property_attributes(property_string):
    attributes = {"type": "any", "getter": None, "setter": None}
    attributes.update(cfml_functions.parse_attributes(property_string))

    for key in ["getter", "setter"]:
        if attributes[key] in ["true", "yes"]:
            attributes[key] = True
        elif attributes[key] in ["false", "no"]:
            attributes[key] = False

    return attributes
