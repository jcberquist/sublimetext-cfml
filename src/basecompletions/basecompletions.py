import sublime
import json
from .. import utils

COMPLETION_FILES = ["cfml_tags", "cfml_functions", "cfml_member_functions"]
DOC_STYLES = {
    "side_color": "#4C9BB0",
    "header_color": "#306B7B",
    "header_bg_color": "#E4EEF1",
    "text_color": "#272B33"
}

completions = {}
function_names = []
cgi = {}


def get_tags(cfml_view):
    return cfml_view.CompletionList(completions["cfml_tags"], 0, False)


def get_tag_attributes(cfml_view):
    if not cfml_view.tag_name:
        return None

    if cfml_view.tag_in_script and not cfml_view.tag_name.startswith("cf"):
        cfml_view.tag_name = "cf" + cfml_view.tag_name

    # tag attribute value completions
    if cfml_view.tag_attribute_name:
        if (
            cfml_view.tag_name in completions["cfml_tag_attribute_values"]
            and cfml_view.tag_attribute_name in completions["cfml_tag_attribute_values"][cfml_view.tag_name]
        ):
            completion_list = completions["cfml_tag_attribute_values"][cfml_view.tag_name][cfml_view.tag_attribute_name]
            return cfml_view.CompletionList(completion_list, 0, False)
        return None

    # tag attribute completions
    if cfml_view.previous_char in [" ", "(", "\t", "\n"]:
        completion_list = completions["cfml_tag_attributes"].get(cfml_view.tag_name, None)
        if completion_list:
            return cfml_view.CompletionList(completion_list, 0, False)

    return None


def get_script_completions(cfml_view):
    completion_list = []

    if cfml_view.view.match_selector(cfml_view.position, "meta.function-call.parameters.cfml,meta.function-call.parameters.method.cfml"):
        completion_list.append(("argumentCollection\tparameter struct", "argumentCollection = ${1:parameters}"))

    completion_list.extend(completions["cfml_functions"][utils.get_setting("cfml_bif_completions")])
    completion_list.extend(completions["cfml_cf_tags_in_script"])
    completion_list.extend(completions["cfml_tags_in_script"])
    return cfml_view.CompletionList(completion_list, 0, False)


def get_dot_completions(cfml_view):

    if len(cfml_view.dot_context) == 1 and cfml_view.dot_context[0].name == "cgi":
        return cfml_view.CompletionList(completions["cgi"], 1, True)

    completion_list = completions["cfml_member_functions"][utils.get_setting("cfml_bif_completions")]
    return cfml_view.CompletionList(completion_list, 0, False)


def get_inline_documentation(cfml_view):

    if cfml_view.view.match_selector(cfml_view.position, "meta.property.constant"):
        word = cfml_view.view.word(cfml_view.position)
        dot_context = cfml_view.get_dot_context(word.begin() - 1)
        if len(dot_context) == 1 and dot_context[0].name == "cgi":
            key = "cgi." + cfml_view.view.substr(word).lower()
            if key in cgi:
                doc = dict(DOC_STYLES)
                doc.update(cgi[key])
                return cfml_view.Documentation(doc, None, 1)

    return None


def load_completions():
    global completions, function_names, cgi
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
    completions["cfml_functions"] = {"basic": [], "required": [], "full": []}
    function_names = []
    for funct in sorted(completions_data["cfml_functions"].keys()):
        completions["cfml_functions"]["basic"].append((funct + '\tfn (cfml)', funct + "($0)"))
        completions["cfml_functions"]["required"].append((funct + '\tfn (cfml)', funct + completions_data["cfml_functions"][funct][0]))
        completions["cfml_functions"]["full"].append((funct + '\tfn (cfml)', funct + completions_data["cfml_functions"][funct][1]))
        function_names.append(funct)

    # member functions
    completions["cfml_member_functions"] = {"basic": [], "required": [], "full": []}
    for member_function_type in sorted(completions_data["cfml_member_functions"].keys()):
        for funct in sorted(completions_data["cfml_member_functions"][member_function_type].keys()):
            completions["cfml_member_functions"]["basic"].append((funct + '\t' + member_function_type + '.fn (cfml)', funct + "($0)"))
            completions["cfml_member_functions"]["required"].append((funct + '\t' + member_function_type + '.fn (cfml)', funct + completions_data["cfml_member_functions"][member_function_type][funct][0]))
            completions["cfml_member_functions"]["full"].append((funct + '\t' + member_function_type + '.fn (cfml)', funct + completions_data["cfml_member_functions"][member_function_type][funct][1]))

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
