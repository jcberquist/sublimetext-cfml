from functools import partial
from .. import model_index
from .. import utils
from ..inline_documentation import Documentation
from ..goto_cfml_file import GotoCfmlFile
from . import cfc_utils

STYLES = {
	"side_color": "#4C9BB0",
	"header_color": "#306B7B",
	"header_bg_color": "#E4EEF1",
	"text_color": "#272B33"
}

def get_inline_documentation(view, position):
	project_name = utils.get_project_name(view)

	if not project_name:
		return None

	cfc_path, file_path, dot_path, function_name = find_cfc(view, position, project_name)

	if file_path:
		if dot_path:
			if function_name:
				metadata = model_index.get_extended_metadata_by_file_path(project_name, file_path)
				if function_name in metadata["functions"]:
					header = dot_path.split(".").pop() + "." + metadata["functions"][function_name].name + "()"
					doc, callback = model_index.get_method_documentation(view, project_name, file_path, function_name, header)
					return Documentation(doc, callback, 2)
			doc, callback = model_index.get_documentation(view, project_name, file_path, dot_path)
			return Documentation(doc, callback, 2)
		doc, callback = get_documentation(view, file_path, cfc_path)
		return Documentation(doc, callback, 2)
	return None

def get_goto_cfml_file(view, position):
	project_name = utils.get_project_name(view)

	if not project_name:
		return None

	cfc_path, file_path, dot_path, function_name = find_cfc(view, position, project_name)

	if file_path:
		if function_name:
			metadata = model_index.get_extended_metadata_by_file_path(project_name, file_path)
			if function_name in metadata["functions"]:
				return GotoCfmlFile(metadata["function_file_map"][function_name], metadata["functions"][function_name].name)
		else:
			return GotoCfmlFile(file_path, None)

	return None

def on_navigate(view, file_path, href):
	view.window().open_file(file_path)

def get_documentation(view, file_path, header):
	cfc_doc = dict(STYLES)
	cfc_doc["links"] = []

	cfc_doc["header"] = header
	cfc_doc["description"] = "<strong>path</strong>: <a class=\"alt-link\" href=\"__go_to_component\">" + file_path + "</a>"


	callback = partial(on_navigate, view, file_path)
	return cfc_doc, callback

def find_cfc(view, position, project_name):
	"""
	returns cfc_path, file_path, dot_path, function_name
	"""
	if view.match_selector(position, "entity.other.inherited-class.cfml"):
		r = utils.get_scope_region_containing_point(view, position, "entity.other.inherited-class.cfml")
		cfc_path = view.substr(r)
		file_path, dot_path = get_cfc_file_info(view, project_name, cfc_path)
		return cfc_path, file_path, dot_path, None

	if view.match_selector(position, "meta.support.function-call.createcomponent.cfml"):
		r = utils.get_scope_region_containing_point(view, position, "meta.support.function-call.createcomponent.cfml")
		cfc_path = cfc_utils.get_component_name(view.substr(r))
		file_path, dot_path = get_cfc_file_info(view, project_name, cfc_path)
		return cfc_path, file_path, dot_path, None

	if view.match_selector(position, "meta.instance.constructor.cfml"):
		r = utils.get_scope_region_containing_point(view, position, "meta.instance.constructor.cfml")
		cfc_path = view.substr(r)[4:].split("(")[0]
		file_path, dot_path = get_cfc_file_info(view, project_name, cfc_path)
		return cfc_path, file_path, dot_path, None

	if view.match_selector(position, "string.quoted.single.cfml, string.quoted.double.cfml"):
		cfc_path = view.substr(view.extract_scope(position))
		if cfc_path[0] in ["\"", "'"]:
			cfc_path = cfc_path[1:-1]
		if cfc_utils.is_cfc_dot_path(cfc_path):
			file_path, dot_path = get_cfc_file_info(view, project_name, cfc_path)
			return cfc_path, file_path, dot_path, None

	if view.match_selector(position, "meta.function-call.method"):
		function_name, function_name_region, function_args_region = utils.get_function_call(view, position)
		if view.substr(function_name_region.begin() - 1) == ".":
			dot_context = utils.get_dot_context(view, function_name_region.begin() - 1)

			if view.match_selector(dot_context[-1].name_region.begin(), "meta.instance.constructor.cfml"):
				r = utils.get_scope_region_containing_point(view, dot_context[-1].name_region.begin(), "meta.instance.constructor.cfml")
				cfc_path = view.substr(r)[4:].split("(")[0]
				file_path, dot_path = get_cfc_file_info(view, project_name, cfc_path)
				return cfc_path, file_path, dot_path, function_name

			if view.match_selector(dot_context[-1].name_region.begin(), "meta.support.function-call.createcomponent.cfml"):
				r = utils.get_scope_region_containing_point(view, dot_context[-1].name_region.begin(), "meta.support.function-call.createcomponent.cfml")
				cfc_path = cfc_utils.get_component_name(view.substr(r))
				file_path, dot_path = get_cfc_file_info(view, project_name, cfc_path)
				return cfc_path, file_path, dot_path, function_name

	return None, None, None, None

def get_cfc_file_info(view, project_name, cfc_path):
	if not cfc_path:
		return None, None

	cfc_dot_path = model_index.get_file_path_by_dot_path(project_name, cfc_path.lower())
	if not cfc_dot_path:
		folder_cfc_path = cfc_utils.get_folder_cfc_path(view, project_name, cfc_path)
		if folder_cfc_path:
			cfc_dot_path = model_index.get_file_path_by_dot_path(project_name, folder_cfc_path.lower())

	if cfc_dot_path:
		return cfc_dot_path["file_path"], cfc_dot_path["dot_path"]

	# at this point, we know the cfc dot path is not one that is indexed in the model index
	# but we might be able to find it via mappings
	if view.window().project_file_name():
		mappings = view.window().project_data().get("mappings", [])
		mapped_cfc_path = "/" + cfc_path.lower().replace(".", "/") + ".cfc"
		for mapping in mappings:
			normalized_mapping = utils.normalize_mapping(mapping)
			if mapped_cfc_path.lower().startswith(normalized_mapping["mapping"]):
				relative_path = mapped_cfc_path.replace(normalized_mapping["mapping"], "")[1:]
				relative_path, path_exists = utils.get_verified_path(normalized_mapping["path"], relative_path)
				if path_exists:
					full_file_path = normalized_mapping["path"] + "/" + relative_path
					return full_file_path, None

	# last option is to do a relative search from the directory of the current file
	if view.file_name():
		normalized_path = utils.normalize_path(view.file_name())
		directory = "/".join(normalized_path.split("/")[:-1])
		relative_path, path_exists = utils.get_verified_path(directory, cfc_path.lower().replace(".", "/") + ".cfc")
		if path_exists:
			full_file_path = directory + "/" + relative_path
			return full_file_path, None

	return None, None