import sublime
import json
from ..completions import CompletionList
from ..inline_documentation import Documentation
from .. import utils

COMPLETION_FILES = ["cfml_tags","cfml_functions","cfml_member_functions"]
DOC_STYLES = {
	"side_color": "#4C9BB0",
	"header_color": "#306B7B",
	"header_bg_color": "#E4EEF1",
	"text_color": "#272B33"
}

completions = {}
cgi = {}

def get_tags(view, prefix, position, info):
	completion_list = completions["cfml_tags"]
	return CompletionList(completion_list, 0, False)

def get_tag_attributes(view, prefix, position, info):
	if not info["tag_name"]:
		return None

	if info["tag_in_script"] and not info["tag_name"].startswith("cf"):
		 info["tag_name"] = "cf" + info["tag_name"]

	# tag attribute value completions
	if info["tag_attribute_name"]:
		if (info["tag_name"] in completions["cfml_tag_attribute_values"]
				and info["tag_attribute_name"] in completions["cfml_tag_attribute_values"][info["tag_name"]]):
			completion_list = completions["cfml_tag_attribute_values"][info["tag_name"]][info["tag_attribute_name"]]
			return CompletionList(completion_list, 0, False)
		return None

	# tag attribute completions
	if info["previous_char"] in [" ", "(", "\t", "\n"]:
		completion_list = completions["cfml_tag_attributes"].get(info["tag_name"], None)
		if completion_list:
			return CompletionList(completion_list, 0, False)

	return None

def get_script_completions(view, prefix, position, info):
	completion_list = []
	completion_list.extend(completions["cfml_functions"])
	completion_list.extend(completions["cfml_cf_tags_in_script"])
	completion_list.extend(completions["cfml_tags_in_script"])
	return CompletionList(completion_list, 0, False)

def get_dot_completions(view, prefix, position, info):

	if len(info["dot_context"]) == 1 and info["dot_context"][0].name == "cgi":
		return CompletionList(completions["cgi"], 1, True)

	completion_list = completions["cfml_member_functions"]
	return CompletionList(completion_list, 0, False)

def get_inline_documentation(view, position):

	if view.match_selector(position, "meta.property.constant"):
		word = view.word(position)
		dot_context = utils.get_dot_context(view, word.begin() - 1)
		if len(dot_context) == 1 and dot_context[0].name == "cgi":
			key = "cgi." + view.substr(word).lower()
			if key in cgi:
				doc = dict(DOC_STYLES)
				doc.update(cgi[key])
				return Documentation(doc, None, 1)

	return None

def load_completions():
	global completions, cgi
	completions_data = {filename: load_json_data(filename) for filename in COMPLETION_FILES}

	# tags
	completions["cfml_tags"] = []
	completions["cfml_tags_in_script"] = []
	completions["cfml_cf_tags_in_script"] = []
	completions["cfml_tag_attributes"] = {}
	completions["cfml_tag_attribute_values"] = {}
	for tag_name in sorted(completions_data["cfml_tags"].keys()):
		if isinstance(completions_data["cfml_tags"][tag_name], list):
			completions_data["cfml_tags"][tag_name] = {"attributes": completions_data["cfml_tags"][tag_name], "attribute_values": {}}
		tag_attributes = completions_data["cfml_tags"][tag_name]["attributes"]
		completions["cfml_tags"].append(make_tag_completion(tag_name, tag_attributes[0]))
		completions["cfml_tags_in_script"].append(make_tag_completion(tag_name[2:], tag_attributes[0]))
		completions["cfml_cf_tags_in_script"].append(make_cf_script_tag_completion(tag_name, tag_attributes[0]))
		completions["cfml_tag_attributes"][tag_name] = [(a + '\trequired', a + '="$1"') for a in tag_attributes[0]]
		completions["cfml_tag_attributes"][tag_name].extend([(a + '\toptional', a + '="$1"') for a in tag_attributes[1]])
		# attribute values
		tag_attribute_values = completions_data["cfml_tags"][tag_name]["attribute_values"]
		completions["cfml_tag_attribute_values"][tag_name] = {}
		for attribute_name in sorted(tag_attribute_values.keys()):
			completions["cfml_tag_attribute_values"][tag_name][attribute_name] = [(v + '\t' + attribute_name, v) for v in tag_attribute_values[attribute_name]]

	# functions
	completions["cfml_functions"] = [(funct + '\tfn (cfml)', funct + completions_data["cfml_functions"][funct]) for funct in sorted(completions_data["cfml_functions"].keys())]

	# member functions
	mem_func_comp = []
	for member_function_type in sorted(completions_data["cfml_member_functions"].keys()):
		for funct in sorted(completions_data["cfml_member_functions"][member_function_type].keys()):
			mem_func_comp.append( (funct + '\t' + member_function_type + '.fn (cfml)', funct + completions_data["cfml_member_functions"][member_function_type][funct]))
	completions["cfml_member_functions"] = mem_func_comp

	# CGI scope
	cgi = load_json_data("cgi")
	completions["cgi"] = [(scope_variable.split(".").pop().upper() + "\tCGI", scope_variable.split(".").pop().upper()) for scope_variable in sorted(cgi.keys())]

def load_json_data(filename):
	json_data = sublime.load_resource("Packages/" + utils.get_plugin_name() + "/src/basecompletions/json/" + filename + ".json")
	return json.loads(json_data)

def make_tag_completion(tag, required_attrs):
	attrs = ''
	for index, attr in enumerate(required_attrs, 1):
		attrs += ' ' + attr + '="$' + str(index) + '"'
	return (tag + '\ttag (cfml)', tag + attrs)

def make_cf_script_tag_completion(tag, required_attrs):
	attrs = []
	for index, attr in enumerate(required_attrs, 1):
		attrs.append(' ' + attr + '="$' + str(index) + '"')
	return (tag + '\ttag (cfml)', tag + "(" + ",".join(attrs) + "$0 )")
