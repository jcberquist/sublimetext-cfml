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


def index(file_string, cfscript_range=None, hidden_tags=None):
    if cfscript_range is None:
        cfscript_range = ranges.RangeWalker(file_string, 0, 'cfscript').walk()
    if cfscript_range is None:
        # only an empty file has no script range
        return {}
    if hidden_tags is None:
        hidden_tags = ranges.TagText(file_string)

    properties = {}
    for property_match in re.finditer(regex.cfml_property, file_string):
        # the match starts with the line's indentation, so check the ranges
        # at the keyword itself
        property_string = property_match.group().lstrip()
        keyword_pt = property_match.end() - len(property_string)

        if property_string.lower().startswith('<cf'):
            if hidden_tags.contains(keyword_pt):
                continue
        else:
            if cfscript_range.is_in_range(keyword_pt, ranges.NON_SCRIPT_RANGES):
                continue

            # a script property belongs directly in the component body
            dr = cfscript_range.deepest_range(keyword_pt)
            if dr is None or dr.name != 'curly_brackets' or dr.depth() != 1:
                continue

        property_string = property_match.group(1)

        # search for 'property type name;' syntax
        type_name_search = re.search(regex.property_type_name, property_string)
        if type_name_search:
            property_string = property_string.replace(type_name_search.group(0), '')

        attributes = find_property_attributes(property_string)

        if type_name_search:
            attributes['name'] = type_name_search.group(2)
        if type_name_search and type_name_search.group(1):
            attributes['type'] = type_name_search.group(1)

        # an empty name, as `property name=""` has while it is typed, is
        # not a property
        if attributes.get('name'):
            property_name = attributes['name']
            del attributes['name']
            properties[property_name] = attributes
    return properties


def find_property_attributes(property_string):
    attributes = {'type': 'any', 'getter': None, 'setter': None}
    attributes.update(cfml_functions.parse_attributes(property_string))

    for key in ['getter', 'setter']:
        if attributes[key] in ['true', 'yes']:
            attributes[key] = True
        elif attributes[key] in ['false', 'no']:
            attributes[key] = False

    return attributes
