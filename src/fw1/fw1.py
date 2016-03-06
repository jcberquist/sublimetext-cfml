import json, sublime, webbrowser
from os.path import dirname, realpath
from ..completions import CompletionList
from ..inline_documentation import Documentation
from .. import utils

DOC_STYLES = {
	"side_color": "#2BA361",
	"header_color": "#3C9959",
	"header_bg_color": "#CFECD8",
	"text_color": "#585B31"
}

fw1 = {"settings": {}, "settings_docs": {}, "methods": {}, "methods_docs": {}}

def plugin_loaded():
	sublime.set_timeout_async(load)

def load():
	global fw1
	for key in fw1:
		data = load_json_data(key)
		if key == "settings":
			data = {k: make_setting_completions(k, data[k]) for k in data}
		elif key == "methods":
			data["calls"] = [(key + "\tframework.one", key.split("(")[0] + data["calls"][key]) for key in sorted(data["calls"].keys())]
			data["definitions"] = [(key + "\tframework.one", key.split("(")[0] + data["definitions"][key]) for key in sorted(data["definitions"].keys())]
			data["renderdata"] = [(key + "\trenderData()", key.split("(")[0] + data["renderdata"][key]) for key in sorted(data["renderdata"].keys())]
		fw1[key] = data

def load_json_data(filename):
	json_data = sublime.load_resource("Packages/" + utils.get_plugin_name() + "/src/fw1/json/" + filename + ".json")
	return json.loads(json_data)

def make_setting_completions(prefix, source_list):
	return [(key + "\t" + prefix, key) for key in sorted(source_list)]

def get_setting(view, setting_key):
	if view.window().project_file_name() and setting_key in view.window().project_data():
		return view.window().project_data()[setting_key]
	package_settings = sublime.load_settings("cfml_package.sublime-settings")
	return package_settings.get(setting_key)

def extends_fw1(view):
	extends_regions = view.find_by_selector("entity.other.inherited-class.cfml")
	if len(extends_regions) > 0:
		extends = view.substr(extends_regions[0])
		return extends.lower() == "framework.one"
	return False

def get_file_type(view):
	if not view.file_name():
		return ""
	file_path = view.file_name().replace("\\", "/").lower()
	for file_type in ["view","layout","controller"]:
		for folder in get_setting(view, "fw1_" + file_type + "_folders"):
			if "/" + folder in file_path:
				return file_type
	return ""

def get_dot_completions(view, prefix, position, info):
	if not get_setting(view, "fw1_enabled") or len(info["dot_context"]) == 0:
		return None

	if extends_fw1(view):
		if info["dot_context"][-1].name == "variables":
			key = ".".join([symbol.name for symbol in reversed(info["dot_context"])])
			if key in fw1["settings"]:
				return CompletionList(fw1["settings"][key], 1, False)
		if info["dot_context"][-1].name in ["renderdata","renderer"]:
			return CompletionList(fw1["methods"]["renderdata"], 1, False)

	if  get_file_type(view) == "controller":
		if len(info["dot_context"]) > 1 and info["dot_context"][-2].name in ["renderdata","renderer"]:
			return CompletionList(fw1["methods"]["renderdata"], 1, False)
		if info["dot_context"][-1].name in ["fw","framework"]:
			return CompletionList(fw1["methods"]["calls"], 1, False)

	return None

def get_script_completions(view, prefix, position, info):
	if not get_setting(view, "fw1_enabled"):
		return None

	if extends_fw1(view):
		if view.match_selector(position, "meta.class.body.cfml -meta.function.body -meta.struct-literal"):
			return CompletionList(fw1["methods"]["definitions"], 1, False)

		key = get_struct_var_assignment(view, position)
		completions = []
		if key and key in fw1["settings"]:
			return CompletionList(fw1["settings"][key], 1, False)

		return CompletionList(fw1["methods"]["calls"], 1, False)

	if get_file_type(view) in ["view","layout"]:
		return CompletionList(fw1["methods"]["calls"], 1, False)

	return None

def get_inline_documentation(view, position):
	if not get_setting(view, "fw1_enabled"):
		return None

	view_extends_fw1 = extends_fw1(view)
	view_file_type = get_file_type(view)

	# settings
	context = []
	word_region = view.word(position)

	if view_extends_fw1 and view.match_selector(position, "meta.property"):
		context = utils.get_dot_context(view, word_region.begin() - 1)

	if view_extends_fw1 and view.match_selector(position, "meta.class.body.cfml meta.struct-literal.cfml"):
		context = utils.get_struct_context(view, position)

	if len(context) > 0:
		key = ".".join([symbol.name for symbol in reversed(context)])
		if view.match_selector(position, "meta.property,meta.struct-literal.key,variable.other"):
			key += "." + view.substr(word_region).lower()
		if key in fw1["settings_docs"]:
			return Documentation(get_documentation(key, fw1["settings_docs"][key]), None, 2)
		parent_key = ".".join(key.split(".")[:-1])
		if parent_key in fw1["settings_docs"]:
			return Documentation(get_documentation(parent_key, fw1["settings_docs"][parent_key]), None, 2)

	# methods
	if view_extends_fw1 and view.match_selector(position, "meta.function.declaration.cfml"):
		function_name, function_name_region, function_region = utils.get_function(view, position)
		if function_name in fw1["methods_docs"]:
			return Documentation(get_documentation(function_name, fw1["methods_docs"][function_name]), None, 2)

	if view_extends_fw1 or view_file_type in ["view","layout"]:
		if view.match_selector(position, "meta.function-call"):
			function_name, function_name_region, function_args_region = utils.get_function_call(view, position)
			if function_name in fw1["methods_docs"]:
				return Documentation(get_documentation(function_name, fw1["methods_docs"][function_name]), None, 2)

	if view_file_type == "controller" and view.match_selector(position, "meta.function-call.method"):
			function_name, function_name_region, function_args_region = utils.get_function_call(view, position)
			if view.substr(function_name_region.begin() - 1) == ".":
				dot_context = utils.get_dot_context(view, function_name_region.begin() - 1)
				if dot_context[-1].name in ["fw","framework"] and function_name in fw1["methods_docs"]:
					return Documentation(get_documentation(function_name, fw1["methods_docs"][function_name]), None, 2)

	return None

def get_documentation(key, metadata):
	fw1_doc = dict(DOC_STYLES)
	fw1_doc["header"] = metadata["header"]
	fw1_doc["description"] = metadata["description"]
	fw1_doc["body"] = metadata["body"]
	fw1_doc["links"] = metadata["links"]
	return fw1_doc

def get_struct_var_assignment(view, pt):
	struct_context = utils.get_struct_context(view, pt)
	variable_name = ".".join([symbol.name for symbol in reversed(struct_context)])
	return variable_name
