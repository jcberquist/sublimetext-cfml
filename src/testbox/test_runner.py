# thanks to the Default Package - Default/exec.py

import sublime, sublime_plugin
import json, os, re, time, urllib.request
from functools import partial
from .. import utils

SYNTAX_EXT = "sublime-syntax" if int(sublime.version()) >= 3092 else "hidden-tmLanguage"
RESULTS_TEMPLATES = {"logo": "","bundle": "", "results": "","global_exception": "", "legend": ""}

def plugin_loaded():
	sublime.set_timeout_async(load)

def load():
	global RESULTS_TEMPLATES
	for template in RESULTS_TEMPLATES:
		RESULTS_TEMPLATES[template] = sublime.load_resource("Packages/" + utils.get_plugin_name() + "/templates/testbox/" + template + ".txt").replace("\r", "")

class TestboxCommand(sublime_plugin.WindowCommand):

	def run(self, cmd = None, test_type=""):

		if not len(self.get_setting("testbox_runner_url")):
			sublime.message_dialog("No TestBox runner URL has been defined for this project.")
			return

		testbox_tests_root = self.normalize_directory(self.get_setting("testbox_tests_root"))

		directory, filename, ext = self.get_path_parts(self.window.active_view().file_name())
		full_url = self.get_setting("testbox_runner_url")
		test_bundle = ""

		if test_type in ["directory","cfc"]:
			if not directory.startswith(testbox_tests_root):
				print(testbox_tests_root, directory)
				sublime.message_dialog("\"testbox_tests_root\" is missing, cannot determine dotted path for directory.")
				return
			full_url += self.get_dotted_directory(testbox_tests_root, directory)
		else:
			full_url += self.get_setting("testbox_default_directory")

		if test_type == "cfc":
			if ext != "cfc":
				sublime.message_dialog("Invalid file type, only \"cfc\" extension is valid for TestBox tests.")
				return
			test_bundle = self.get_dotted_directory(testbox_tests_root, directory) + "." + filename
			full_url += "&testBundles=" + test_bundle

		if not hasattr(self, "output_view"):
			self.output_view = self.window.create_output_panel("testbox")

		testbox_results = {k: self.normalize_directory(v) for k, v in self.get_setting("testbox_results").items()}

		self.output_view.settings().set("result_file_regex", testbox_results["server_root"] + "([^\\s].*):([0-9]+)$")
		self.output_view.settings().set("result_base_dir", testbox_results["sublime_root"])
		self.output_view.settings().set("word_wrap", True)
		self.output_view.settings().set("line_numbers", False)
		self.output_view.settings().set("gutter", False)
		self.output_view.settings().set("scroll_past_end", False)
		self.output_view.settings().set("color_scheme", "Packages/" + utils.get_plugin_name() + "/color-schemes/testbox.hidden-tmTheme")
		self.output_view.assign_syntax("Packages/" + utils.get_plugin_name() + "/syntaxes/testbox." + SYNTAX_EXT)

		# As per Default/exec.py
		# Call create_output_panel a second time after assigning the above
		# settings, so that it'll be picked up as a result buffer
		self.window.create_output_panel("testbox")

		self.window.run_command("show_panel", {"panel": "output.testbox"})
		self.output_view.run_command("append", {"characters": RESULTS_TEMPLATES["logo"], "force": True, "scroll_to_end": True})

		# run async
		sublime.set_timeout_async(partial(self.run_tests, full_url, test_bundle))

	def run_tests(self, full_url, test_bundle):
		sublime.status_message("TestBox: running tests")
		print("TestBox: " + full_url)

		try:
			json_string = urllib.request.urlopen(full_url).read().decode("utf-8")
			result_string = render_result(json.loads(json_string), test_bundle)
		except:
			result_string = "\nError when trying to fetch:\n" + full_url
			result_string += "\nPlease verify the URL is valid and returns the test results in JSON."

		self.output_view.run_command("append", {"characters": result_string, "force": True, "scroll_to_end": False})

	def get_setting(self, setting_key):
		if setting_key in self.window.project_data():
			return self.window.project_data()[setting_key]
		package_settings = sublime.load_settings("cfml_package.sublime-settings")
		return package_settings.get(setting_key, "")

	def get_path_parts(self, file_name):
		normalized_file_name = file_name.replace("\\","/")
		file_parts = normalized_file_name.split("/")
		directory = "/".join(file_parts[:-1]) + "/"
		file_and_ext = file_parts[-1].split(".")
		return directory, file_and_ext[0], file_and_ext[1]

	def get_dotted_directory(self, root, directory):
		return directory.replace(root, "").replace("/",".")[:-1]

	def normalize_directory(self, directory):
		if len(directory) == 0:
			return ""
		normalized_directory = directory.replace("\\", "/")
		if normalized_directory[-1] != "/":
			normalized_directory += "/"
		return normalized_directory

# result rendering

def render_result(result_data, test_bundle):
	# lowercase all the keys since we can't guarantee the casing coming from CFML
	result_data = lcase_keys(result_data)
	result_string = sublime.expand_variables(RESULTS_TEMPLATES["results"], filter_stats_dict(result_data)) + "\n"

	for bundle in result_data["bundlestats"]:
		if len(test_bundle) and bundle["path"] != test_bundle:
			continue

		result_string += "\n" + sublime.expand_variables(RESULTS_TEMPLATES["bundle"], filter_stats_dict(bundle)) + "\n"

		if isinstance(bundle["globalexception"], dict):
			result_string += "\n" + sublime.expand_variables(RESULTS_TEMPLATES["global_exception"], filter_exception_dict(bundle["globalexception"])) + "\n"

		for suite in bundle["suitestats"]:
			result_string += "\n" + gen_suite_report(suite)

	result_string += "\n" + RESULTS_TEMPLATES["legend"]
	return result_string

def lcase_keys(source):
	if isinstance(source, dict):
		return {k.lower(): lcase_keys(source[k]) for k in source}
	if isinstance(source, list):
		return [lcase_keys(item) for item in source]
	return source

def filter_stats_dict(source):
	stat_keys = ["path","totalduration","totalbundles","totalsuites","totalspecs"]
	stat_keys.extend(["totalpass","totalfail","totalerror","totalskipped"])
	return {key: str(source[key]) for key in stat_keys if key in source}

def filter_exception_dict(source):
	exception_keys = ["type","message","detail","stacktrace"]
	return {key: str(source[key]) for key in exception_keys if key in source}

def get_status_bit(status):
	status_dict = {"Failed": "!", "Error": "X", "Skipped": "-"}
	if status in status_dict:
		return status_dict[status]
	return "+"

def build_stacktrace(stack, tabs):
	stacktrace = ""
	for row in stack:
		stacktrace += tabs + "     " + row["template"] + ":" + str(row["line"]) + "\n"
	return stacktrace

def gen_suite_report(suiteStats, level=0):
	tabs = "    " * level
	report = tabs + "(" + get_status_bit(suiteStats["status"]) + ")" + suiteStats["name"] + "\n"
	level += 1
	for spec in suiteStats["specstats"]:
		tabs = "    " * level
		report += tabs + "(" + get_status_bit(spec["status"]) + ")" + spec["name"] + " (" + str(spec["totalduration"]) + " ms)" + "\n"

		if spec["status"] == "Failed":
			report += tabs + "  -> Failure: " + spec["failmessage"] + "\n"
			report += build_stacktrace(spec["failorigin"], tabs)

		if spec["status"] == "Error":
			report += tabs + "  -> Error: " + spec["error"]["message"] + "\n"
			if "tagcontext" in spec["error"]:
				report += build_stacktrace(spec["error"]["tagcontext"], tabs)

	for nestedSuite in suiteStats["suitestats"]:
		report += gen_suite_report(nestedSuite, level + 1) + "\n"

	return report
