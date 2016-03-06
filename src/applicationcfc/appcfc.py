import sublime
import json
from ..completions import CompletionList
from ..inline_documentation import Documentation
from .. import utils

DOC_STYLES = {
	"side_color": "#4C9BB0",
	"header_color": "#306B7B",
	"header_bg_color": "#E4EEF1",
	"text_color": "#272B33"
}

appcfc = {"settings": {}, "settings_docs": {}, "methods": {}, "methods_docs": {}}

def plugin_loaded():
	sublime.set_timeout_async(load)

def load():
	global appcfc
	for key in appcfc:
		data = load_json_data(key)
		if key == "settings":
			data = {k: make_setting_completions(k, data[k]) for k in data}
		elif key == "methods":
			data = [(key + "\tapplication.cfc", key + data[key]) for key in sorted(data.keys())]
		appcfc[key] = data

def make_setting_completions(prefix, source_list):
	return [(key + "\t" + prefix, key) for key in sorted(source_list)]

def load_json_data(filename):
	json_data = sublime.load_resource("Packages/" + utils.get_plugin_name() + "/src/applicationcfc/json/" + filename + ".json")
	return json.loads(json_data)

def get_dot_completions(view, prefix, position, info):
	if info["file_name"] == "application.cfc" and len(info["dot_context"]) > 0 and info["dot_context"][-1].name == "this":
		key = ".".join([symbol.name for symbol in reversed(info["dot_context"])])
		if key in appcfc["settings"]:
			return CompletionList(appcfc["settings"][key], 1, False)

	return None

def get_script_completions(view, prefix, position, info):
	if info["file_name"] == "application.cfc":
		if view.match_selector(position, "meta.class.body.cfml -meta.function"):
			return CompletionList(appcfc["methods"], 1, False)

		key = get_struct_var_assignment(view, position)
		if key and key in appcfc["settings"]:
			return CompletionList(appcfc["settings"][key], 1, False)

	return None

def get_inline_documentation(view, position):
	file_name = view.file_name().replace("\\", "/").split("/").pop().lower() if view.file_name() else ""
	if file_name != "application.cfc":
		return None

	# settings
	context = []
	word_region = view.word(position)

	if view.match_selector(position, "meta.property"):
		context = utils.get_dot_context(view, word_region.begin() - 1)

	if view.match_selector(position, "meta.class.body.cfml meta.struct-literal.cfml"):
		context = utils.get_struct_context(view, position)

	if len(context) > 0:
		key = ".".join([symbol.name for symbol in reversed(context)])
		if view.match_selector(position, "meta.property, meta.struct-literal.key.cfml, variable.other.readwrite.cfml"):
			key += "." + view.substr(word_region).lower()
		if key in appcfc["settings_docs"]:
			return Documentation(get_documentation(key, appcfc["settings_docs"][key]), None, 1)
		parent_key = ".".join(key.split(".")[:-1])
		if parent_key in appcfc["settings_docs"]:
			return Documentation(get_documentation(parent_key, appcfc["settings_docs"][parent_key]), None, 1)

	# methods
	if view.match_selector(position, "meta.function.cfml"):
		function_name, function_name_region, function_region = utils.get_function(view, position)
		if function_name in appcfc["methods_docs"]:
			return Documentation(get_documentation(function_name, appcfc["methods_docs"][function_name]), None, 1)

	return None

def get_documentation(key, metadata):
	appcfc_doc = dict(DOC_STYLES)
	appcfc_doc["header"] = metadata["header"]
	appcfc_doc["description"] = metadata["description"]
	appcfc_doc["links"] = [{"href": "http://cfdocs.org/application-cfc", "text": "cfdocs.org/application-cfc"}]
	appcfc_doc["links"].extend(metadata["links"])
	return appcfc_doc

def get_struct_var_assignment(view, pt):
	struct_context = utils.get_struct_context(view, pt)
	variable_name = ".".join([symbol.name for symbol in reversed(struct_context)])
	return variable_name
