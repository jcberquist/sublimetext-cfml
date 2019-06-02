import sublime
import re
from ... import documentation_helpers
from ... import utils
from ... import cfdocs

SIDE_COLOR = "#158CBA"

CFDOCS_ENGINES = {"coldfusion": "ColdFusion", "lucee": "Lucee", "openbd": "OpenBD"}


def get_inline_documentation(cfml_view, doc_type):
    doc_name = None
    doc_attr_or_arg = None
    doc_regions = None
    doc_priority = 0

    if not utils.get_setting("cfdocs_enabled"):
        return None

    # tags
    if cfml_view.tag_name:
        doc_name = cfml_view.tag_name
        doc_attr_or_arg = cfml_view.tag_attribute_name

        if (
            doc_type == "hover_doc"
            and doc_name in ["cfcomponent", "cfinterface", "cffunction"]
            and cfml_view.view.match_selector(cfml_view.position, "source.cfml.script")
        ):
            return None

    # functions
    elif cfml_view.view.match_selector(
        cfml_view.position, "meta.function-call.support.cfml"
    ):
        doc_name, function_name_region, function_args_region = cfml_view.get_function_call(
            cfml_view.position, True
        )
        doc_regions = [
            sublime.Region(function_name_region.begin(), function_args_region.end())
        ]

    if doc_name:
        data, success = cfdocs.get_cfdoc(doc_name)
        if success:
            return cfml_view.Documentation(
                doc_regions,
                build_cfdoc(doc_name, doc_attr_or_arg, data),
                None,
                doc_priority,
            )
        return cfml_view.Documentation(
            doc_regions, build_cfdoc_error(doc_name, data), None, doc_priority
        )

    return None


def get_completion_docs(cfml_view):
    if not utils.get_setting("cfdocs_enabled"):
        return None

    if (
        cfml_view.tag_name
        and cfml_view.tag_attribute_name
        and cfml_view.tag_location == "tag_attributes"
    ):
        data, success = cfdocs.get_cfdoc(cfml_view.tag_name)
        if success:
            for param in data["params"]:
                if param["name"].lower() == cfml_view.tag_attribute_name.lower():

                    return cfml_view.CompletionDoc(
                        None, build_tag_completion_doc(data, param), None
                    )
        return None

    if (
        cfml_view.function_call_params
        and cfml_view.function_call_params.support
        and not cfml_view.function_call_params.method
    ):
        data, success = cfdocs.get_cfdoc(cfml_view.function_call_params.function_name)
        if success:
            return cfml_view.CompletionDoc(
                None,
                build_function_completion_doc(cfml_view.function_call_params, data),
                None,
            )

    return None


def get_goto_cfml_file(cfml_view):
    # functions
    if cfml_view.view.match_selector(
        cfml_view.position, "meta.function-call.support.cfml"
    ):
        doc_name, function_name_region, function_args_region = cfml_view.get_function_call(
            cfml_view.position, True
        )

    # tags
    elif cfml_view.view.match_selector(
        cfml_view.position, "meta.tag.cfml,meta.tag.script.cfml,meta.tag.script.cf.cfml"
    ):
        doc_name = utils.get_tag_name(cfml_view.view, cfml_view.position)
        if doc_name and doc_name[:2] != "cf":
            # tag in script
            doc_name = "cf" + doc_name

    else:
        return None

    if doc_name:
        return cfml_view.GotoCfmlFile("https://cfdocs.org/" + doc_name, None)

    return None


def build_engine_span(engine, minimum_version):
    span = '<span class="' + engine + '">&nbsp;' + CFDOCS_ENGINES[engine]
    if len(minimum_version) > 0:
        span += " " + minimum_version + "+"
    span += "&nbsp;</span>&nbsp;"
    return span


def build_cfdoc(function_or_tag, attr_or_arg, data):
    cfdoc = {"side_color": SIDE_COLOR, "html": {}}
    cfdoc["html"]["links"] = [
        {
            "href": "https://cfdocs.org" + "/" + function_or_tag,
            "text": "cfdocs.org" + "/" + function_or_tag,
        }
    ]
    cfdoc["html"]["header"] = build_cfdoc_header(data, attr_or_arg)

    cfdoc["html"]["body"] = '<div class="engines">'
    for engine in sorted(CFDOCS_ENGINES):
        if engine not in data["engines"]:
            continue
        cfdoc["html"]["body"] += build_engine_span(
            engine, data["engines"][engine]["minimum_version"]
        )
    cfdoc["html"]["body"] += "</div>"

    for param in data["params"]:
        if attr_or_arg and param["name"].lower() == attr_or_arg.lower():
            header, body = build_attr_doc(param)
            cfdoc["html"]["body"] += documentation_helpers.card(header, body)
            cfdoc["html"]["body"] += "\n"
            break
    else:
        cfdoc["html"]["body"] += documentation_helpers.card(
            body=documentation_helpers.clean_html(data["description"])
        )

        if len(data["params"]) > 0:
            cfdoc["html"]["body"] += (
                "<h2>ARGUMENT REFERENCE</h2>"
                if data["type"] == "function"
                else "<h2>ATTRIBUTE REFERENCE</h2>"
            )
            for param in data["params"]:
                header, body = build_attr_doc(param)
                cfdoc["html"]["body"] += documentation_helpers.card(header, body)
                cfdoc["html"]["body"] += "\n"

    cfdoc["html"]["body"] = re.sub(
        r"`([^`\n<>]+)`", r'<span class="code">\1</span>', cfdoc["html"]["body"]
    )

    return cfdoc


def build_attr_doc(param):
    header = documentation_helpers.param_header(param)
    body = ""
    if "default" in param and len(str(param["default"])):
        body += (
            '<p><em>Default:</em> <span class="code">'
            + str(param["default"])
            + "</span></p>"
        )
    description = (
        param["description"].replace("\n ", "<br>").replace("\n", "<br>").strip()
    )
    if len(description) > 0:
        body += "<p>" + description + "</p>"
    if "values" in param and len(param["values"]):
        body += (
            "<p><em>values:</em> "
            + ", ".join([str(value) for value in param["values"]])
            + "</p>"
        )

    return header, body


def build_cfdoc_header(data, attr_or_arg=None, include_params=True):
    if data["type"] != "function":
        header = "&lt;" + documentation_helpers.span_wrap(
            data["name"], "entity.name.tag.cfml"
        )
        for param in data["params"]:
            if attr_or_arg:
                if attr_or_arg.lower() != param["name"].lower():
                    continue
            elif not include_params or "required" not in param or not param["required"]:
                continue
            header += (
                " "
                + documentation_helpers.span_wrap(
                    param["name"], "entity.other.attribute-name"
                )
                + '=""'
            )

        header += "&gt;"
        return header

    header = documentation_helpers.span_wrap(data["name"], "entity.name.function")
    header += "("

    param_base = ""
    if include_params:
        for param in data["params"]:
            span_html = param_base + documentation_helpers.span_wrap(
                param["name"], "variable.parameter.function"
            )

            if "required" not in param or not param["required"]:
                span_html = "[" + span_html + "]"

            param_base = ", "
            header += span_html
    else:
        header += "..." if len(data["params"]) > 0 else ""

    header += ")"

    if len(data["returns"]) > 0:
        header += ": " + documentation_helpers.span_wrap(
            data["returns"], "storage.type"
        )

    return header


def build_cfdoc_error(function_or_tag, data):
    cfdoc = {"side_color": SIDE_COLOR, "html": {}}
    cfdoc["html"]["side_color"] = "#F2777A"
    cfdoc["html"]["header_bg_color"] = "#FFFFFF"
    cfdoc["html"]["header"] = "Uh oh!"
    cfdoc["html"]["body"] = "I tried to load that doc for you but got this instead:<br>"
    cfdoc["html"]["body"] += data["error_message"]

    return cfdoc


def build_function_completion_doc(function_call_params, data):
    cfdoc = {"side_color": SIDE_COLOR, "html": {}}
    cfdoc["html"]["header"] = build_cfdoc_header(data, include_params=False)

    cfdoc["html"]["body"] = ""

    description_params = []
    if len(data["params"]) > 0:
        for index, param in enumerate(data["params"]):

            if function_call_params.named_params:
                active_name = (
                    function_call_params.params[function_call_params.current_index][0]
                    or ""
                )
                is_active = active_name.lower() == param["name"].lower()
            else:
                is_active = index == function_call_params.current_index

            if is_active:
                param_variables = {
                    "name": param["name"],
                    "description": param["description"].replace("\n", "<br>"),
                    "values": "",
                }
                if "type" in param and len(param["type"]):
                    param_variables["name"] += ": " + param["type"]
                if "values" in param and len(param["values"]):
                    param_variables["values"] = "<em>values:</em> " + ", ".join(
                        [str(value) for value in param["values"]]
                    )
                if (
                    len(param_variables["description"]) > 0
                    or len(param_variables["values"]) > 0
                ):
                    cfdoc["html"]["body"] = sublime.expand_variables(
                        "<p>${description}</p><p>${values}</p>", param_variables
                    )
                description_params.append(
                    '<span class="active">' + param["name"] + "</span>"
                )
            elif param["required"]:
                description_params.append(
                    '<span class="required">' + param["name"] + "</span>"
                )
            else:
                description_params.append(
                    '<span class="optional">' + param["name"] + "</span>"
                )

        cfdoc["html"]["arguments"] = "(" + ", ".join(description_params) + ")"

    return cfdoc


def build_tag_completion_doc(data, param):
    cfdoc = {"side_color": SIDE_COLOR, "html": {}}
    cfdoc["html"]["header"] = build_cfdoc_header(data, include_params=False)

    header, body = build_attr_doc(param)
    cfdoc["html"]["body"] = body
    cfdoc["html"]["arguments"] = documentation_helpers.param_header(param)
    return cfdoc
