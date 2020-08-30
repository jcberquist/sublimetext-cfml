import sublime
import json
from ... import utils
from ... import cfdocs


COMPLETION_FILES = [
    "cfml_tags",
    "cfml_functions",
    "cfml_member_functions",
    "cfml_function_params",
]


SIDE_COLOR = "color(#4C9BB0 blend(var(--background) 60%))"


completions = {}
function_names = []
cgi = {}


def get_tags(cfml_view):
    return cfml_view.CompletionList(completions["cfml_tags"], 0, False)


def get_tag_attributes(cfml_view):
    if not cfml_view.tag_name:
        return None

    if (
        cfml_view.tag_attribute_name is None
        or cfml_view.tag_location == "tag_attribute_name"
    ):
        # tag attribute completions
        completion_list = completions["cfml_tag_attributes"].get(
            cfml_view.tag_name, None
        )
        if completion_list:
            return cfml_view.CompletionList(completion_list, 0, False)
    elif (
        cfml_view.tag_name in completions["cfml_tag_attribute_values"]
        and cfml_view.tag_attribute_name
        in completions["cfml_tag_attribute_values"][cfml_view.tag_name]
    ):
        # tag attribute value completions
        completion_list = completions["cfml_tag_attribute_values"][cfml_view.tag_name][
            cfml_view.tag_attribute_name
        ]
        return cfml_view.CompletionList(completion_list, 0, False)

    return None


def get_script_completions(cfml_view):
    completion_list = []

    if cfml_view.view.match_selector(
        cfml_view.position,
        "meta.function-call.parameters.cfml,meta.function-call.parameters.method.cfml",
    ):
        completion_list.append(
            sublime.CompletionItem(
                "argumentCollection",
                "parameter struct",
                "argumentCollection = ${1:parameters}",
                sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_ID_VARIABLE, "v", "CFML"),
            )
        )

    if cfml_view.view.match_selector(
        cfml_view.position, "source.cfml.script meta.function-call.parameters"
    ):
        param_completions = get_param_completions(cfml_view)
        if param_completions:
            completion_list.extend(param_completions)
            return cfml_view.CompletionList(completion_list, 0, False)

    completion_list.extend(
        completions["cfml_functions"][utils.get_setting("cfml_bif_completions")]
    )
    completion_list.extend(completions["cfml_cf_tags_in_script"])
    completion_list.extend(completions["cfml_tags_in_script"])
    return cfml_view.CompletionList(completion_list, 0, False)


def get_dot_completions(cfml_view):

    if len(cfml_view.dot_context) == 1 and cfml_view.dot_context[0].name == "cgi":
        return cfml_view.CompletionList(completions["cgi"], 0, False)

    completion_list = completions["cfml_member_functions"][
        utils.get_setting("cfml_bif_completions")
    ]
    return cfml_view.CompletionList(completion_list, 0, False)


def get_inline_documentation(cfml_view, doc_type):

    if cfml_view.view.match_selector(cfml_view.position, "meta.property.constant"):
        word = cfml_view.view.word(cfml_view.position)
        dot_context = cfml_view.get_dot_context(word.begin() - 1)
        if len(dot_context) == 1 and dot_context[0].name == "cgi":
            key = "cgi." + cfml_view.view.substr(word).lower()
            if key in cgi:
                doc = {"side_color": SIDE_COLOR, "html": {}}
                doc["html"].update(cgi[key])
                return cfml_view.Documentation([word], doc, None, 1)

    return None


def load_completions():
    global completions, function_names, cgi
    completions_data = {
        filename: load_json_data(filename) for filename in COMPLETION_FILES
    }

    # tags
    completions["cfml_tags"] = []
    completions["cfml_tags_in_script"] = []
    completions["cfml_cf_tags_in_script"] = []
    completions["cfml_tag_attributes"] = {}
    completions["cfml_tag_attribute_values"] = {}
    for tag_name in sorted(completions_data["cfml_tags"].keys()):
        if isinstance(completions_data["cfml_tags"][tag_name], list):
            completions_data["cfml_tags"][tag_name] = {
                "attributes": completions_data["cfml_tags"][tag_name],
                "attribute_values": {},
            }
        tag_attributes = completions_data["cfml_tags"][tag_name]["attributes"]
        completions["cfml_tags"].append(
            make_tag_completion(tag_name, tag_attributes[0])
        )
        completions["cfml_tags_in_script"].append(
            make_tag_completion(tag_name[2:], tag_attributes[0])
        )
        completions["cfml_cf_tags_in_script"].append(
            make_cf_script_tag_completion(tag_name, tag_attributes[0])
        )
        completions["cfml_tag_attributes"][tag_name] = [
            sublime.CompletionItem(
                a,
                "required",
                a + '="$1"',
                sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_ID_MARKUP, "a", tag_name),
            )
            for a in tag_attributes[0]
        ]
        completions["cfml_tag_attributes"][tag_name].extend(
            [
                sublime.CompletionItem(
                    a,
                    "optional",
                    a + '="$1"',
                    sublime.COMPLETION_FORMAT_SNIPPET,
                    kind=(sublime.KIND_ID_MARKUP, "a", tag_name),
                )
                for a in tag_attributes[1]
            ]
        )
        # attribute values
        tag_attribute_values = completions_data["cfml_tags"][tag_name][
            "attribute_values"
        ]
        completions["cfml_tag_attribute_values"][tag_name] = {}
        for attribute_name in sorted(tag_attribute_values.keys()):
            completions["cfml_tag_attribute_values"][tag_name][attribute_name] = [
                sublime.CompletionItem(
                    v,
                    attribute_name,
                    v,
                    sublime.COMPLETION_FORMAT_TEXT,
                    kind=(sublime.KIND_ID_AMBIGUOUS, "v", tag_name),
                )
                for v in tag_attribute_values[attribute_name]
            ]

    # functions
    completions["cfml_functions"] = {"basic": [], "required": [], "full": []}
    function_names = []
    for funct in sorted(completions_data["cfml_functions"].keys()):
        completions["cfml_functions"]["basic"].append(
            sublime.CompletionItem(
                funct,
                "cfml.fn",
                funct + "($0)",
                sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_ID_FUNCTION, "f", "function"),
                details=completions_data["cfml_functions"][funct][0],
            )
        )
        completions["cfml_functions"]["required"].append(
            sublime.CompletionItem(
                funct,
                "cfml.fn",
                funct + completions_data["cfml_functions"][funct][1][0],
                sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_ID_FUNCTION, "f", "function"),
                details=completions_data["cfml_functions"][funct][0],
            )
        )
        completions["cfml_functions"]["full"].append(
            sublime.CompletionItem(
                funct,
                "cfml.fn",
                funct + completions_data["cfml_functions"][funct][1][1],
                sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_ID_FUNCTION, "f", "function"),
                details=completions_data["cfml_functions"][funct][0],
            )
        )

        function_names.append(funct)

    # function params
    completions["cfml_function_params"] = {}
    for funct in sorted(completions_data["cfml_function_params"].keys()):
        completions["cfml_function_params"][funct] = {}
        for param in sorted(completions_data["cfml_function_params"][funct].keys()):
            completions["cfml_function_params"][funct][param] = []
            for value in completions_data["cfml_function_params"][funct][param]:
                completions["cfml_function_params"][funct][param].append(
                    sublime.CompletionItem(
                        value,
                        param,
                        value,
                        kind=(sublime.KIND_ID_AMBIGUOUS, "p", funct),
                    )
                )

    # member functions
    completions["cfml_member_functions"] = {"basic": [], "required": [], "full": []}
    for member_function_type in sorted(
        completions_data["cfml_member_functions"].keys()
    ):
        for funct in sorted(
            completions_data["cfml_member_functions"][member_function_type].keys()
        ):
            completions["cfml_member_functions"]["basic"].append(
                sublime.CompletionItem(
                    funct,
                    member_function_type + ".fn",
                    funct + "($0)",
                    sublime.COMPLETION_FORMAT_SNIPPET,
                    kind=(sublime.KIND_ID_FUNCTION, "m", "method"),
                    details=completions_data["cfml_member_functions"][
                        member_function_type
                    ][funct][0],
                )
            )
            completions["cfml_member_functions"]["required"].append(
                sublime.CompletionItem(
                    funct,
                    member_function_type + ".fn",
                    funct
                    + completions_data["cfml_member_functions"][member_function_type][
                        funct
                    ][1][0],
                    sublime.COMPLETION_FORMAT_SNIPPET,
                    kind=(sublime.KIND_ID_FUNCTION, "m", "method"),
                    details=completions_data["cfml_member_functions"][
                        member_function_type
                    ][funct][0],
                )
            )
            completions["cfml_member_functions"]["full"].append(
                sublime.CompletionItem(
                    funct,
                    member_function_type + ".fn",
                    funct
                    + completions_data["cfml_member_functions"][member_function_type][
                        funct
                    ][1][1],
                    sublime.COMPLETION_FORMAT_SNIPPET,
                    kind=(sublime.KIND_ID_FUNCTION, "m", "method"),
                    details=completions_data["cfml_member_functions"][
                        member_function_type
                    ][funct][0],
                )
            )

    # CGI scope
    cgi = load_json_data("cgi")
    completions["cgi"] = [
        sublime.CompletionItem(
            scope_variable.split(".").pop().upper(),
            "CGI Scope",
            kind=(sublime.KIND_ID_VARIABLE, "c", "CFML"),
        )
        for scope_variable in sorted(cgi.keys())
    ]


def load_json_data(filename):
    json_data = sublime.load_resource(
        "Packages/"
        + utils.get_plugin_name()
        + "/src/plugins_/basecompletions/json/"
        + filename
        + ".json"
    )
    return json.loads(json_data)


def make_tag_completion(tag, required_attrs):
    attrs = ""
    for index, attr in enumerate(required_attrs, 1):
        attrs += " " + attr + '="$' + str(index) + '"'
    return sublime.CompletionItem(
        tag,
        "tag (cfml)",
        tag + attrs,
        sublime.COMPLETION_FORMAT_SNIPPET,
        kind=(sublime.KIND_ID_MARKUP, "t", "CFML"),
    )


def make_cf_script_tag_completion(tag, required_attrs):
    attrs = []
    for index, attr in enumerate(required_attrs, 1):
        attrs.append(" " + attr + '="$' + str(index) + '"')
    return sublime.CompletionItem(
        tag,
        "tag (cfml)",
        tag + "(" + ",".join(attrs) + "$0 )",
        sublime.COMPLETION_FORMAT_SNIPPET,
        kind=(sublime.KIND_ID_MARKUP, "t", "CFML"),
    )


def get_param_completions(cfml_view):
    if (
        not cfml_view.function_call_params
        or not cfml_view.function_call_params.support
        or cfml_view.function_call_params.method
        or cfml_view.function_call_params.function_name
        not in completions["cfml_function_params"]
    ):
        return None

    data, success = cfdocs.get_cfdoc(cfml_view.function_call_params.function_name)
    if not success:
        return None

    active_param = get_active_param(data["params"], cfml_view.function_call_params)
    if not active_param:
        return None

    if (
        active_param
        not in completions["cfml_function_params"][
            cfml_view.function_call_params.function_name
        ]
    ):
        return None

    return completions["cfml_function_params"][
        cfml_view.function_call_params.function_name
    ][active_param]


def get_active_param(params, function_call_params):
    if len(params) > 0:
        for index, param in enumerate(params):
            if function_call_params.named_params:
                active_name = (
                    function_call_params.params[function_call_params.current_index][0]
                    or ""
                )
                is_active = active_name.lower() == param["name"].lower()
            else:
                is_active = index == function_call_params.current_index
            if is_active:
                return param["name"].lower()
    return None
