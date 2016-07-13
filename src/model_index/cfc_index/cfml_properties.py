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
from . import cfml_functions
from . import regex


def index(file_string):
    properties = {}
    for property_string in re.findall(regex.cfml_property, file_string):

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
