from .. import utils
from ..inline_documentation import Documentation
from ..goto_cfml_file import GotoCfmlFile
from . import cfcs
from .. import model_index

def get_inline_documentation(view, position):
	project_name = utils.get_project_name(view)

	if not project_name:
		return None

	cfc_info, metadata, function_name = find_cfc(view, position, project_name)

	if cfc_info:
		if function_name:
			header = cfc_info["name"] + "." + metadata["functions"][function_name].name + "()"
			doc, callback = model_index.get_method_documentation(view, project_name, cfc_info["file_path"], function_name, header)
		else:
			doc, callback = model_index.get_documentation(view, project_name, cfc_info["file_path"], cfc_info["name"])
		return Documentation(doc, callback, 2)

	return None

def get_goto_cfml_file(view, position):
	project_name = utils.get_project_name(view)

	if not project_name:
		return None

	cfc_info, metadata, function_name = find_cfc(view, position, project_name)

	if cfc_info:
		if function_name:
			return GotoCfmlFile(cfc_info["file_path"], metadata["functions"][function_name].name)
		else:
			return GotoCfmlFile(cfc_info["file_path"], None)

	return None


def find_cfc(view, position, project_name):
	if view.match_selector(position, "meta.function-call.method"):
		function_name, function_name_region, function_args_region = utils.get_function_call(view, position)
		if view.substr(function_name_region.begin() - 1) == ".":
			dot_context = utils.get_dot_context(view, function_name_region.begin() - 1)
			symbol_name = None
			# check for known cfc name
			for symbol in dot_context:
				if not symbol.is_function and cfcs.has_cfc(project_name, symbol.name):
					symbol_name = symbol.name
					break
			# also check for getter being used to access cfc
			if not symbol_name:
				symbol = dot_context[-1]
				if symbol.is_function and symbol.name.startswith("get") and cfcs.has_cfc(project_name, symbol.name[3:]):
					symbol_name = symbol.name[3:]

			if symbol_name:
				cfc_info = cfcs.get_cfc_info(project_name, symbol_name)
				metadata = cfcs.get_cfc_metadata(project_name, symbol_name)
				if function_name in metadata["functions"]:
					return cfc_info, metadata, function_name

	# check for cfc
	cfc_name = None
	if view.match_selector(position, "variable.other.object.cfml, meta.tag.property.name.cfml"):
		cfc_name = view.substr(view.word(position)).lower()
	elif view.match_selector(position, "meta.function-call.cfml variable.function.cfml"):
		var_name = view.substr(view.word(position)).lower()
		if var_name.startswith("get"):
			cfc_name = var_name[3:]

	if cfc_name and cfcs.has_cfc(project_name, cfc_name):
		metadata = cfcs.get_cfc_metadata(project_name, cfc_name)
		cfc_info = cfcs.get_cfc_info(project_name, cfc_name)
		return cfc_info, metadata, None

	return None, None, None