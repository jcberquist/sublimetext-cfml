import sublime, re
from ..completions import CompletionList
from .. import utils

def get_script_completions(view, prefix, position, info):
	if not info["file_name"] or not info["file_name"].endswith(".cfc"):
		return None
	cfc_property_names = {view.substr(r) for r in view.find_by_selector("meta.tag.property.name.cfml")}
	cfc_property_names = sorted([name[0].upper() + name[1:] for name in cfc_property_names if name])
	if len(cfc_property_names) > 0:
		completion_list = [make_completion(property_name, "getter") for property_name in cfc_property_names]
		completion_list.extend([make_completion(property_name, "setter") for property_name in cfc_property_names])
		return CompletionList(completion_list, 0, False)

	return None

def make_completion(property_name, accessor_type):
	if accessor_type == "getter":
		return ("get" + property_name + "()\tgetter", "get" + property_name + "()")
	return ("set" + property_name + "()\tsetter", "set" + property_name + "($1)$0")
