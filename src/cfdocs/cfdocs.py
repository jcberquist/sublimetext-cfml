import sublime
import json
import urllib.request
import urllib.error
from .. import utils

CFDOCS_CACHE = {}

CFDOCS_PARAM_TEMPLATE = '<strong>${name}</strong><p>${description}</p><p>${values}</p>'
CFDOCS_BASE_URL = "https://raw.githubusercontent.com/foundeo/cfdocs/master/data/en/"

CFDOCS_STYLES = {
    "side_color": "#18BC9C",
    "header_color": "#C7254E",
    "header_bg_color": "#F9F2F4",
    "text_color": "#272B33"
}

CFDOCS_ENGINES = {
    "coldfusion": "ColdFusion",
    "lucee": "Lucee",
    "openbd": "OpenBD"
}


def get_inline_documentation(cfml_view, doc_type):
    doc_name = None
    doc_regions = None
    doc_priority = 0

    # functions
    if cfml_view.view.match_selector(cfml_view.position, "meta.function-call.support.cfml"):
        doc_name, function_name_region, function_args_region = cfml_view.get_function_call(cfml_view.position, True)
        doc_regions = [sublime.Region(function_name_region.begin(), function_args_region.end())]

    # tags
    elif cfml_view.view.match_selector(cfml_view.position, "meta.tag.cfml,meta.tag.script.cfml,meta.tag.script.cf.cfml"):
        doc_name = utils.get_tag_name(cfml_view.view, cfml_view.position)
        if doc_name and doc_name[:2] != "cf":
            # tag in script
            doc_name = "cf" + doc_name

    elif doc_type == "hover_doc":
        return None

    # script component, interface, function
    elif cfml_view.view.match_selector(cfml_view.position, "meta.class.declaration.cfml"):
        doc_name = "cfcomponent"
    elif cfml_view.view.match_selector(cfml_view.position, "meta.interface.declaration.cfml"):
        doc_name = "cfinterface"
    elif cfml_view.view.match_selector(cfml_view.position, "meta.function.declaration.cfml"):
        doc_name = "cffunction"

    if doc_name:
        data, success = get_cfdoc(doc_name)
        if success:
            return cfml_view.Documentation(doc_regions, build_cfdoc(doc_name, data), None, doc_priority)
        return cfml_view.Documentation(doc_regions, build_cfdoc_error(doc_name, data), None, doc_priority)

    return None


def get_completion_docs(cfml_view):
    if cfml_view.function_call_params is None:
        return None

    if cfml_view.function_call_params.support and not cfml_view.function_call_params.method:
        return get_completion_doc(cfml_view)

    return None


def get_completion_doc(cfml_view):
    data, success = get_cfdoc(cfml_view.function_call_params.function_name)
    if success:
        return cfml_view.CompletionDoc(None, build_completion_doc(cfml_view.function_call_params, data), None)
    return None


def get_cfdoc(function_or_tag):
    if utils.get_setting("cfdocs_path"):
        return load_cfdoc(function_or_tag)
    return fetch_cfdoc(function_or_tag)


def load_cfdoc(function_or_tag):
    global CFDOCS_CACHE
    file_path = function_or_tag + ".json"
    if file_path not in CFDOCS_CACHE:
        full_file_path = utils.normalize_path(utils.get_setting("cfdocs_path")) + "/" + file_path
        try:
            with open(full_file_path, "r", encoding="utf-8") as f:
                json_string = f.read()
        except:
            data = {"error_message": "Unable to read " + function_or_tag + ".json"}
            return data, False
        try:
            data = json.loads(json_string)
        except ValueError as e:
            data = {"error_message": "Unable to decode " + function_or_tag + ".json<br>ValueError: " + str(e)}
            return data, False

        CFDOCS_CACHE[file_path] = data

    return CFDOCS_CACHE[file_path], True


def fetch_cfdoc(function_or_tag):
    global CFDOCS_CACHE
    file_path = function_or_tag + ".json"

    if file_path not in CFDOCS_CACHE:
        full_url = CFDOCS_BASE_URL + file_path
        try:
            json_string = urllib.request.urlopen(full_url).read().decode("utf-8")
        except urllib.error.HTTPError as e:
            data = {"error_message": "Unable to fetch " + function_or_tag + ".json<br>" + str(e)}
            return data, False

        try:
            data = json.loads(json_string)
        except ValueError as e:
            data = {"error_message": "Unable to decode " + function_or_tag + ".json<br>ValueError: " + str(e)}
            return data, False

        CFDOCS_CACHE[file_path] = data

    return CFDOCS_CACHE[file_path], True


def build_engine_span(engine, minimum_version):
    span = "<span class=\"" + engine + "\">&nbsp;" + CFDOCS_ENGINES[engine]
    if len(minimum_version) > 0:
        span += " " + minimum_version + "+"
    span += "&nbsp;</span>&nbsp;"
    return span


def build_cfdoc(function_or_tag, data):
    cfdoc = dict(CFDOCS_STYLES)
    cfdoc["links"] = [{"href": "http://cfdocs.org" + "/" + function_or_tag, "text": "cfdocs.org" + "/" + function_or_tag}]
    cfdoc["header"] = data["syntax"].replace("<", "&lt;").replace(">", "&gt;")
    if len(data["returns"]) > 0:
        cfdoc["header"] += ":" + data["returns"]

    cfdoc["description"] = "<div class=\"engines\">"
    for engine in sorted(CFDOCS_ENGINES):
        if engine not in data["engines"]:
            continue
        cfdoc["description"] += build_engine_span(engine, data["engines"][engine]["minimum_version"])
    cfdoc["description"] += "</div>"

    cfdoc["description"] += data["description"].replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

    cfdoc["body"] = ""
    if len(data["params"]) > 0:
        cfdoc["body"] = "<ul>"
        for param in data["params"]:
            param_variables = {"name": param["name"], "description": param["description"].replace("\n", "<br>"), "values": ""}
            if "values" in param and len(param["values"]):
                param_variables["values"] = "<em>values:</em> " + ", ".join([str(value) for value in param["values"]])
            cfdoc["body"] += "<li>" + sublime.expand_variables(CFDOCS_PARAM_TEMPLATE, param_variables) + "</li>"
        cfdoc["body"] += "</ul>"

    return cfdoc


def build_cfdoc_error(function_or_tag, data):
    cfdoc = dict(CFDOCS_STYLES)
    cfdoc["side_color"] = "#F2777A"
    cfdoc["header_bg_color"] = "#FFFFFF"
    cfdoc["header"] = "Uh oh!"
    cfdoc["description"] = "I tried to load that doc for you but got this instead:"
    cfdoc["body"] = data["error_message"]

    return cfdoc


def build_completion_doc(function_call_params, data):
    cfdoc = dict(CFDOCS_STYLES)
    cfdoc["header"] = data["syntax"].split('(')[0] + "(...)"
    if len(data["returns"]) > 0:
        cfdoc["header"] += ":" + data["returns"]

    cfdoc["description"] = ""
    cfdoc["body"] = ""
    description_params = []
    if len(data["params"]) > 0:
        for index, param in enumerate(data["params"]):

            if function_call_params.named_params:
                active_name = function_call_params.params[function_call_params.current_index][0] or ""
                is_active = active_name.lower() == param["name"].lower()
            else:
                is_active = index == function_call_params.current_index

            if is_active:
                param_variables = {"name": param["name"], "description": param["description"].replace("\n", "<br>"), "values": ""}
                if "values" in param and len(param["values"]):
                    param_variables["values"] = "<em>values:</em> " + ", ".join([str(value) for value in param["values"]])
                if len(param_variables["description"]) > 0 or len(param_variables["values"]) > 0:
                    cfdoc["body"] = sublime.expand_variables("<p>${description}</p><p>${values}</p>", param_variables)
                description_params.append("<span class=\"active\">" + param["name"] + "</span>")
            elif param["required"]:
                description_params.append("<span class=\"required\">" + param["name"] + "</span>")
            else:
                description_params.append("<span class=\"optional\">" + param["name"] + "</span>")

        cfdoc["description"] = "(" + ", ".join(description_params) + ")"

    return cfdoc
