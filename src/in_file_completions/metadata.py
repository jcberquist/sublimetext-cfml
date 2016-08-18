from .. import utils
from ..model_index.cfc_index import parse_cfc_file_string
from ..model_index import get_file_path_by_dot_path, get_extended_metadata_by_file_path, resolve_path

def get_view_metadata(view):
	file_string = get_minimal_file_string(view)
	base_meta = parse_cfc_file_string(file_string)

	extended_meta = dict(base_meta)
	extended_meta.update({"functions": {}, "function_file_map": {}, "properties": {}, "property_file_map": {}})

	file_path = utils.normalize_path(view.file_name()) if view.file_name() else ""
	project_name = utils.get_project_name(view)
	if project_name and base_meta["extends"]:
		extends_file_path = resolve_path(project_name, file_path, base_meta["extends"])
		root_meta = get_extended_metadata_by_file_path(project_name, extends_file_path)
		if root_meta:
			for key in ["functions", "function_file_map", "properties", "property_file_map"]:
				extended_meta[key].update(root_meta[key])

	extended_meta["functions"].update(base_meta["functions"])
	extended_meta["function_file_map"].update({funct_key: file_path for funct_key in base_meta["functions"]})
	extended_meta["properties"].update(base_meta["properties"])
	extended_meta["property_file_map"].update({prop_key: file_path for prop_key in base_meta["properties"]})
	return extended_meta

def get_string_metadata(file_string):
	return parse_cfc_file_string(file_string)

def get_minimal_file_string(view):
	min_string = ""

	tag_component_regions = view.find_by_selector("meta.class.cfml")

	if len(tag_component_regions) > 0:
		min_string += view.substr(tag_component_regions[0]) + "\n"
		current_funct = ""
		for r in view.find_by_selector("meta.function.cfml, meta.function.body.tag.cfml meta.tag.argument.cfml"):
			text = view.substr(r)
			if text.lower().startswith("<cff") and len(current_funct) > 0:
				min_string += current_funct + "</cffunction>\n"
				current_funct = ""
			current_funct += text + "\n"
		min_string += current_funct + "</cffunction>\n"
	else:
		script_selectors = [
			("comment.block.documentation.cfml -meta.class", "\n"),
			("meta.class.declaration.cfml", " {\n"),
			("meta.tag.property.cfml", ";\n")
		]

		for selector, separator in script_selectors:
			for r in view.find_by_selector(selector):
				min_string += view.substr(r) + separator

		funct_regions = "meta.class.body.cfml comment.block.documentation.cfml, meta.function.declaration.cfml -meta.function.body.cfml"
		for r in view.find_by_selector(funct_regions):
			string = view.substr(r)
			min_string += string + ("\n" if string.endswith("*/") else "\{ \}\n")

	return min_string
