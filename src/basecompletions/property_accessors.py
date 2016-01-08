import sublime, re
from ..completions import CompletionList
from .. import utils

prop_name_regex = re.compile("(?i)name\s*=\s*[\"']?([a-z\.0-9\$]+)\\b")

def get_script_completions(view, prefix, position, info):
	if not info["file_name"] or not info["file_name"].endswith(".cfc"):
		return None
	# start with unquoted props
	cfc_property_names = {view.substr(r) for r in view.find_by_selector("meta.tag.property.name.cfml")}
	cfc_property_names.update({find_property_name(view.substr(r)) for r in view.find_by_selector("meta.tag.property.cfml")})

	cfc_property_names = sorted([name[0].upper() + name[1:] for name in cfc_property_names if name])
	if len(cfc_property_names) > 0:
		completion_list = [make_completion(property_name, "getter") for property_name in cfc_property_names]
		completion_list.extend([make_completion(property_name, "setter") for property_name in cfc_property_names])
		return CompletionList(completion_list, 0, False)

	return None

def find_property_name(property_tag_string):
	name_search = re.search(prop_name_regex, property_tag_string)
	if name_search:
		return name_search.group(1)
	return None

def make_completion(property_name, accessor_type):
	if accessor_type == "getter":
		return ("get" + property_name + "()\tgetter", "get" + property_name + "()")
	return ("set" + property_name + "()\tsetter", "set" + property_name + "($1)$0")
