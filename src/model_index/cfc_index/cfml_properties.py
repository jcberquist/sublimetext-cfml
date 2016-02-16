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

script_property_regex = re.compile("^\s*(property[^;>]+);", re.I | re.M)
tag_property_regex = re.compile("^\s*<cf(property[^>]+)>", re.I | re.M)

type_name_regex = re.compile("^property.+?(?:(\w+)\s+)?\\b(\w+)\\b(?:$|\s*\w+\s*=)", re.I | re.M | re.S)

attr_regex = {}
for key in ["name","type","getter","setter"]:
  attr_regex[key] = re.compile(key + "\s*=\s*[\"']?([\w\.]+)", re.I)

def index(file_string):
	properties = {name: attributes for name, attributes in find_script_properties(file_string) if name}
	properties.update({name: attributes for name, attributes in find_tag_properties(file_string) if name})
	return properties

def find_script_properties(file_string):
	return [find_script_property(property_string) for property_string in re.findall(script_property_regex, file_string)]

def find_tag_properties(file_string):
	return [find_tag_property(property_string) for property_string in re.findall(tag_property_regex, file_string)]

def find_script_property(property_string):
	attribute_name = None
	attributes = {}

	# search first for 'property type name;' syntax
	type_name_search = re.search(type_name_regex, property_string)
	if type_name_search:
		attribute_name = type_name_search.group(2)

	if not attribute_name:
		attr_search = re.search(attr_regex["name"], property_string)
		if not attr_search:
			return None, None
		attribute_name = attr_search.group(1)

	attributes.update(find_property_attributes(property_string))

	if type_name_search and type_name_search.group(1):
		attributes["type"] = type_name_search.group(1)

	return attribute_name, attributes

def find_tag_property(property_string):
	attribute_name = None

	attr_search = re.search(attr_regex["name"], property_string)
	if not attr_search:
		return None, None
	attribute_name = attr_search.group(1)

	attributes = find_property_attributes(property_string)
	return attribute_name, attributes


def find_property_attributes(property_string):
	attributes = {"type": "any", "getter": None, "setter": None}

	attr_search = re.search(attr_regex["type"], property_string)
	if attr_search:
		attributes["type"] = attr_search.group(1)

	for key in ["getter","setter"]:
		attr_search = re.search(attr_regex[key], property_string)
		if attr_search:
			prop_value = attr_search.group(1).lower()
			if prop_value in ["true", "yes"]:
				attributes[key] = True
			elif prop_value in ["false", "no"]:
				attributes[key] = False

	return attributes
