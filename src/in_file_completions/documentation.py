import sublime
from functools import partial
from .. import utils, model_index
from ..inline_documentation import Documentation
from ..goto_cfml_file import GotoCfmlFile
from . import metadata
from .in_file_completions import get_extends


SYNTAX_EXT = "sublime-syntax" if int(sublime.version()) >= 3092 else "tmLanguage"


def get_inline_documentation(view, position):
	doc_name = None
	doc_priority = 0

	extended_meta, function_name, header = get_function_info(view, position)

	if extended_meta:
		doc, callback = get_function_documentation(view, extended_meta, function_name, header)
		return Documentation(doc, callback, 2)

	extended_meta, file_path, header = get_cfc_info(view, position)
	if extended_meta:
		doc, callback = get_documentation(view, extended_meta, file_path, header)
		return Documentation(doc, callback, 2)

	return None


def get_goto_cfml_file(view, position):

	extended_meta, function_name, header = get_function_info(view, position)
	if extended_meta:
		return GotoCfmlFile(extended_meta["function_file_map"][function_name], extended_meta["functions"][function_name].name)

	extended_meta, file_path, header = get_cfc_info(view, position)
	if extended_meta:
		return GotoCfmlFile(file_path, None)

	return None


def get_function_info(view, position):
	if view.match_selector(position, "meta.function-call.cfml"):
		function_name, function_name_region, function_args_region = utils.get_function_call(view, position)
		extended_meta = metadata.get_view_metadata(view)
		if function_name in extended_meta["functions"]:
			header = extended_meta["functions"][function_name].name + "()"
			return extended_meta, function_name, header

	if view.match_selector(position, "meta.function-call.method.cfml"):
		function_name, function_name_region, function_args_region = utils.get_function_call(view, position)
		if view.substr(function_name_region.begin() - 1) == ".":
			dot_context = utils.get_dot_context(view, function_name_region.begin() - 1)

			if dot_context[0].name == "this":
				extended_meta = metadata.get_view_metadata(view)
				if function_name in extended_meta["functions"]:
					header = extended_meta["functions"][function_name].name + "()"
					return extended_meta, function_name, header

			if dot_context[0].name == "super":
				project_name = utils.get_project_name(view)
				file_path = utils.normalize_path(view.file_name()) if view.file_name() else ""
				extends = get_extends(view)
				extends_file_path = model_index.resolve_path(project_name, file_path, extends)
				extended_meta = model_index.get_extended_metadata_by_file_path(project_name, extends_file_path)
				if extended_meta and function_name in extended_meta["functions"]:
					header = extended_meta["functions"][function_name].name + "()"
					return extended_meta, function_name, header

	return None, None, None

def get_cfc_info(view, position):
	if view.match_selector(position, "variable.language.this.cfml"):
		extended_meta = metadata.get_view_metadata(view)
		file_path = utils.normalize_path(view.file_name()) if view.file_name() else ""
		return extended_meta, file_path, "this"

	if view.match_selector(position, "variable.language.super.cfml"):
		project_name = utils.get_project_name(view)
		file_path = utils.normalize_path(view.file_name()) if view.file_name() else ""
		extends = get_extends(view)
		extends_file_path = model_index.resolve_path(project_name, file_path, extends)
		extended_meta = model_index.get_extended_metadata_by_file_path(project_name, extends_file_path)
		if extended_meta:
			return extended_meta, extends_file_path, extends

	return None, None, None


def on_navigate(view, file_path, function_file_map, href):

	if href == "__go_to_component":
		if len(file_path) > 2 and file_path[1] == ":":
			file_path = "/" + file_path[0] + file_path[2:]
		view.window().open_file(file_path)
	else:
		file_path = function_file_map[href.lower()]
		if len(file_path) > 2 and file_path[1] == ":":
			file_path = "/" + file_path[0] + file_path[2:]
		view.hide_popup()
		view.window().run_command('cfml_navigate_to_method', {"file_path": file_path, "href": href})

def get_documentation(view, extended_meta, file_path, header):
	model_doc = model_index.build_documentation(extended_meta, file_path, header)
	callback = partial(on_navigate, view, file_path, extended_meta["function_file_map"])
	return model_doc, callback

def get_function_documentation(view, extended_meta, function_name, header):
	function_file_path = extended_meta["function_file_map"][function_name]
	view_file_path = utils.normalize_path(view.file_name()) if view.file_name() else ""
	if len(function_file_path) > 0 and function_file_path != view_file_path:
		with open(function_file_path, "r") as f:
			file_string = f.read()
		cfml_minihtml_view = view.window().create_output_panel("cfml_minihtml")
		cfml_minihtml_view.assign_syntax("Packages/" + utils.get_plugin_name() + "/syntaxes/cfml." + SYNTAX_EXT)
		cfml_minihtml_view.run_command("append", {"characters": file_string, "force": True, "scroll_to_end": True})
		model_doc = model_index.build_method_documentation(extended_meta, function_name, header, cfml_minihtml_view)
		view.window().destroy_output_panel("cfml_minihtml")
	else:
		model_doc = model_index.build_method_documentation(extended_meta, function_name, header, view)

	callback = partial(on_navigate, view, extended_meta["function_file_map"][function_name], extended_meta["function_file_map"])
	return model_doc, callback
