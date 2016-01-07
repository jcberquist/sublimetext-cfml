import json, sublime, webbrowser
from ..completions import CompletionList
from ..inline_documentation import Documentation
from .. import utils

DOC_STYLES = {
	"side_color": "#336B81",
	"header_color": "#379AC1",
	"header_bg_color": "#E1E1E1",
	"text_color": "#585B31"
}

testbox = {"completions": {}, "documentation": {}}

def plugin_loaded():
	sublime.set_timeout_async(load)

def load():
	global testbox

	completions_data = load_json_data("completions")
	for key in completions_data:
		cfc = key.split(".").pop().capitalize()
		if cfc == "Basespec":
			cfc = "BaseSpec"
		testbox["completions"][key] = [(comp_key + "\t" + "TestBox " + cfc, completions_data[key][comp_key]) for comp_key in sorted(completions_data[key].keys())]
		if key == "expectation":
			negated_completions = [(negate_string(comp_key) + "\t" + cfc, negate_string(completions_data[key][comp_key])) for comp_key in sorted(completions_data[key].keys())]
			testbox["completions"][key].extend(negated_completions)


	testbox["documentation"] = load_json_data("documentation")

def load_json_data(filename):
	json_data = sublime.load_resource("Packages/" + utils.get_plugin_name() + "/src/testbox/json/" + filename + ".json")
	return json.loads(json_data)

def negate_string(string_to_negate):
	return "not" + string_to_negate[0].upper() + string_to_negate[1:]

def get_setting(view, setting_key):
	if setting_key in view.window().project_data():
		return view.window().project_data()[setting_key]
	package_settings = sublime.load_settings("cfml_package.sublime-settings")
	return package_settings.get(setting_key)

def extends_testbox(view):
	extends_regions = view.find_by_selector("entity.other.inherited-class.cfml")
	if len(extends_regions) > 0:
		extends = view.substr(extends_regions[0])
		return extends.lower() == "testbox.system.basespec"
	return False

def is_testbox_file(view):
	if extends_testbox(view):
		return True

	if not view.file_name():
		return False

	file_path = view.file_name().replace("\\", "/").lower()
	for folder in get_setting(view, "testbox_folders"):
		if "/" + folder in file_path:
			return True
	return False

def get_dot_completions(view, prefix, position, info):
	if not get_setting(view, "testbox_enabled"):
		return None

	# expectations
	if is_testbox_file(view) and len(info["dot_context"]) > 0 and info["dot_context"][-1].name == "expect":
		return CompletionList(testbox["completions"]["expectation"], 1, False)

	# assertions
	if is_testbox_file(view) and len(info["dot_context"]) == 1 and info["dot_context"][-1].name == "assert":
		return CompletionList(testbox["completions"]["assertion"], 1, False)

	return None

def get_script_completions(view, prefix, position, info):
	if not get_setting(view, "testbox_enabled"):
		return None

	if is_testbox_file(view) and view.match_selector(position, "meta.group.braces.curly"):
		return CompletionList(testbox["completions"]["basespec"], 1, False)

	return None

def get_inline_documentation(view, position):
	if not get_setting(view, "testbox_enabled") or not is_testbox_file(view):
		return None

	if view.match_selector(position, "meta.function-call.method.cfml"):
		function_name, function_name_region, function_args_region = utils.get_function_call(view, position)
		if view.substr(function_name_region.begin() - 1) == ".":
			dot_context = utils.get_dot_context(view, function_name_region.begin() - 1)
			if dot_context[-1].name == "expect":
				if function_name in testbox["documentation"]["expectation"]:
					return Documentation(get_documentation(function_name, testbox["documentation"]["expectation"][function_name]), None, 2)
				if len(function_name) > 3 and function_name[:3] == "not" and function_name[3:] in testbox["documentation"]["expectation"]:
					return Documentation(get_documentation(function_name, testbox["documentation"]["expectation"][function_name[3:]], True), None, 2)
			if dot_context[-1].name == "assert" and function_name in testbox["documentation"]["assertion"]:
				return Documentation(get_documentation(function_name, testbox["documentation"]["assertion"][function_name]), None, 2)

	if view.match_selector(position, "meta.function-call.cfml"):
		function_name, function_name_region, function_args_region = utils.get_function_call(view, position)
		if function_name in testbox["documentation"]["basespec"]:
			return Documentation(get_documentation(function_name, testbox["documentation"]["basespec"][function_name]), None, 2)

	return None

def get_documentation(key, metadata, negated=False):
	testbox_doc = dict(DOC_STYLES)
	testbox_doc["header"] = metadata["header"]
	testbox_doc["description"] = metadata["description"]
	testbox_doc["body"] = metadata["body"]
	testbox_doc["links"] = metadata["links"]

	if negated:
		testbox_doc["header"] += " (negated)"
	return testbox_doc
