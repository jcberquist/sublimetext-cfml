import sublime
import json
import urllib.request
import urllib.error
from .. import utils

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


def get_inline_documentation(cfml_view):
    doc_name = None
    doc_priority = 0

    # functions
    if cfml_view.view.match_selector(cfml_view.position, "meta.function-call.support.cfml"):
        doc_name, function_name_region, function_args_region = cfml_view.get_function_call(cfml_view.position, True)

    # tags
    elif cfml_view.view.match_selector(cfml_view.position, "meta.tag.cfml,meta.tag.script.cfml,meta.tag.script.cf.cfml"):
        doc_name = utils.get_tag_name(cfml_view.view, cfml_view.position)
        if doc_name and doc_name[:2] != "cf":
            # tag in script
            doc_name = "cf" + doc_name

    # script component, interface, function
    elif cfml_view.view.match_selector(cfml_view.position, "meta.class.declaration.cfml"):
        doc_name = "cfcomponent"
    elif cfml_view.view.match_selector(cfml_view.position, "meta.interface.declaration.cfml"):
        doc_name = "cfinterface"
    elif cfml_view.view.match_selector(cfml_view.position, "meta.function.declaration.cfml"):
        doc_name = "cffunction"

    if doc_name:
        return get_cfdoc(doc_name, doc_priority, cfml_view)

    return None


def get_cfdoc(function_or_tag, doc_priority, cfml_view):
    if utils.get_setting("cfdocs_path"):
        data, success = load_cfdoc(function_or_tag)
    else:
        data, success = fetch_cfdoc(function_or_tag)
    if success:
        return cfml_view.Documentation(build_cfdoc(function_or_tag, data), None, doc_priority)
    return cfml_view.Documentation(build_cfdoc_error(function_or_tag, data), None, doc_priority)


def fetch_cfdoc(function_or_tag):
    full_url = CFDOCS_BASE_URL + function_or_tag + ".json"

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

    return data, True


def load_cfdoc(function_or_tag):
    file_path = utils.get_setting("cfdocs_path") + function_or_tag + ".json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json_string = f.read()
    except:
        data = {"error_message": "Unable to read " + function_or_tag + ".json"}
        return data, False
    try:
        data = json.loads(json_string)
    except ValueError as e:
        data = {"error_message": "Unable to decode " + function_or_tag + ".json<br>ValueError: " + str(e)}
        return data, False

    return data, True


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
