import sublime
from functools import partial
from .. import utils, minihtml, documentation_helpers


SIDE_COLOR = "color(var(--bluish) blend(var(--background) 60%))"


def get_documentation(view, extended_metadata, file_path, class_name):
    model_doc = build_documentation(extended_metadata, file_path, class_name)
    callback = partial(
        on_navigate, view, file_path, extended_metadata["function_file_map"]
    )
    return model_doc, callback


def get_method_documentation(
    view,
    extended_metadata,
    file_path,
    function_name,
    class_name,
    method_name,
    method_preview,
):
    model_doc = build_method_documentation(
        extended_metadata, function_name, class_name, method_name, method_preview
    )
    callback = partial(
        on_navigate, view, file_path, extended_metadata["function_file_map"]
    )
    return model_doc, callback


def get_method_preview(
    view, extended_metadata, file_path, function_name, method_preview
):
    model_doc = build_method_preview_doc(
        extended_metadata, function_name, method_preview
    )
    callback = partial(
        on_navigate, view, file_path, extended_metadata["function_file_map"]
    )
    return model_doc, callback


def get_function_call_params_doc(
    extended_metadata, function_call_params, class_name, method_name
):
    model_doc = build_function_call_params_doc(
        extended_metadata, function_call_params, class_name, method_name
    )
    return model_doc, None


def cached_method_preview(view, cache, function_file_path, function_name):
    current_color_scheme = view.settings().get("color_scheme")
    if (
        function_name not in cache
        or cache[function_name]["color_scheme"] != current_color_scheme
    ):
        with open(function_file_path, "r", encoding="utf-8") as f:
            file_string = f.read()
        cfml_minihtml_view = view.window().create_output_panel("cfml_minihtml")
        cfml_minihtml_view.assign_syntax(
            "Packages/" + utils.get_plugin_name() + "/syntaxes/cfml.sublime-syntax"
        )
        cfml_minihtml_view.run_command(
            "append", {"characters": file_string, "force": True, "scroll_to_end": True}
        )
        cache[function_name] = {
            "color_scheme": current_color_scheme,
            "preview": build_method_preview(cfml_minihtml_view, function_name),
        }
        view.window().destroy_output_panel("cfml_minihtml")
    return cache[function_name]["preview"]


def on_navigate(view, file_path, function_file_map, href):
    if href == "__go_to_component":
        if file_path[1] == ":":
            file_path = "/" + file_path[0] + file_path[2:]
        view.window().open_file(file_path)
    else:
        file_path = function_file_map[href.lower()]
        if file_path[1] == ":":
            file_path = "/" + file_path[0] + file_path[2:]
        view.window().run_command(
            "cfml_navigate_to_method", {"file_path": file_path, "href": href}
        )


def build_documentation(extended_metadata, file_path, class_name):
    model_doc = {"side_color": SIDE_COLOR}

    model_doc["html"] = {
        "header": documentation_helpers.span_wrap(class_name, "entity.name.class"),
        "body": "",
        "links": [],
    }

    if file_path:
        model_doc["html"][
            "body"
        ] += """
        <div class="path">
            <strong>path</strong>: <a href="__go_to_component">{}</a>
        </div>
        """.strip().format(
            file_path
        )

    if "hint" in extended_metadata and extended_metadata["hint"]:
        model_doc["html"]["body"] += documentation_helpers.card(
            body=extended_metadata["hint"]
        )

    if "entityname" in extended_metadata and extended_metadata["entityname"]:
        header = documentation_helpers.header(
            "entityname", extended_metadata["entityname"], "string.quoted"
        )
        model_doc["html"]["body"] += documentation_helpers.card(header)

    if "extends" in extended_metadata and extended_metadata["extends"]:
        header = documentation_helpers.header(
            "extends", extended_metadata["extends"], "entity.other.inherited-class"
        )
        model_doc["html"]["body"] += documentation_helpers.card(header)

    for key in ["accessors", "persistent"]:
        if extended_metadata[key]:
            header = documentation_helpers.header(key, "true", "constant.language")
            model_doc["html"]["body"] += documentation_helpers.card(header)

    if len(extended_metadata["properties"]) > 0:
        properties = parse_properties(file_path, extended_metadata)
        if len(properties) > 0:
            model_doc["html"]["body"] += "<h2>Properties</h2>"
            for h, b in properties:
                model_doc["html"]["body"] += documentation_helpers.card(h, b)

    if len(extended_metadata["functions"]) > 0:
        functions = parse_functions(file_path, extended_metadata)
        if "constructor" in functions:
            # we have a constructor
            model_doc["html"]["body"] += "<h2>Constructor</h2>"
            model_doc["html"]["body"] += documentation_helpers.card(
                *functions["constructor"]
            )

        if len(functions["public"]) > 0:
            model_doc["html"]["body"] += "<h2>Public Methods</h2>"
            for h, b in functions["public"]:
                model_doc["html"]["body"] += documentation_helpers.card(h, b)

        if len(functions["private"]) > 0:
            model_doc["html"]["body"] += "<h2>Private Methods</h2>"
            for h, b in functions["private"]:
                model_doc["html"]["body"] += documentation_helpers.card(h, b)

    return model_doc


def build_method_preview(cfml_minihtml_view, function_name):
    function_region = get_function_region(cfml_minihtml_view, function_name)
    css, html = minihtml.from_view(cfml_minihtml_view, function_region)
    return {"css": css, "html": html}


def build_method_documentation(
    extended_metadata, function_name, class_name, method_name, method_preview=None
):
    function_file_path = extended_metadata["function_file_map"][function_name]

    funct = extended_metadata["functions"][function_name]
    model_doc = {"side_color": SIDE_COLOR, "html": {}}
    model_doc["html"]["links"] = []

    model_doc["html"]["header"] = ""
    if class_name:
        model_doc["html"]["header"] += documentation_helpers.span_wrap(
            class_name, "entity.name.class"
        )
        if method_name:
            model_doc["html"]["header"] += "."
    if method_name:
        model_doc["html"]["header"] += (
            documentation_helpers.span_wrap(method_name, "entity.name.function") + "()"
        )
    if funct["meta"]["access"] and len(funct["meta"]["access"]) > 0:
        model_doc["html"]["header"] = (
            documentation_helpers.span_wrap(funct["meta"]["access"], "storage.modifier")
            + " "
            + model_doc["html"]["header"]
        )
    if funct["meta"]["returntype"] and len(funct["meta"]["returntype"]) > 0:
        model_doc["html"]["header"] += ": " + documentation_helpers.span_wrap(
            funct["meta"]["returntype"], "storage.type"
        )

    model_doc["html"][
        "body"
    ] = """
    <div class="path">
        <strong>path</strong>: <a href="{}">{}</a>
    </div>
    """.strip().format(
        funct["name"], function_file_path
    )

    if "hint" in funct["meta"] and funct["meta"]["hint"]:
        model_doc["html"]["body"] += documentation_helpers.card(
            body=funct["meta"]["hint"]
        )

    if len(funct["meta"]["parameters"]) > 0:
        model_doc["html"]["body"] += "<h2>ARGUMENT REFERENCE</h2>"
        for arg in funct["meta"]["parameters"]:
            header = documentation_helpers.param_header(arg)
            body = ""
            if arg["default"]:
                body += (
                    '<p><em>Default:</em> <span class="code">'
                    + str(arg["default"])
                    + "</span></p>"
                )
            if "hint" in arg and arg["hint"]:
                body += arg["hint"]
            model_doc["html"]["body"] += documentation_helpers.card(header, body)
            model_doc["html"]["body"] += "\n"

    if method_preview:
        css = method_preview["css"].replace("<style>", "").replace("</style>", "")
        model_doc["html"]["styles"] = css
        model_doc["html"]["body"] += method_preview["html"]

    return model_doc


def build_method_preview_doc(extended_metadata, function_name, method_preview):
    function_file_path = extended_metadata["function_file_map"][function_name]

    funct = extended_metadata["functions"][function_name]
    preview = {"side_color": SIDE_COLOR, "html": {}}

    preview["html"]["link"] = (
        '<strong>path</strong>: <a class="plain-link" href="'
        + funct["name"]
        + '">'
        + function_file_path
        + "</a>"
    )
    css = method_preview["css"].replace("<style>", "").replace("</style>", "")
    preview["html"]["styles"] = css
    preview["html"]["body"] = method_preview["html"]

    return preview


def build_function_call_params_doc(
    extended_metadata, function_call_params, class_name, method_name
):
    model_doc = {"side_color": SIDE_COLOR, "html": {}}
    funct = extended_metadata["functions"][function_call_params.function_name]

    model_doc["html"]["header"] = ""
    if class_name:
        model_doc["html"]["header"] += documentation_helpers.span_wrap(
            class_name, "entity.name.class"
        )
        if method_name:
            model_doc["html"]["header"] += "."
    if method_name:
        model_doc["html"]["header"] += (
            documentation_helpers.span_wrap(method_name, "entity.name.function") + "()"
        )
    if funct["meta"]["access"] and len(funct["meta"]["access"]) > 0:
        model_doc["html"]["header"] = (
            documentation_helpers.span_wrap(funct["meta"]["access"], "storage.modifier")
            + " "
            + model_doc["html"]["header"]
        )
    if funct["meta"]["returntype"] and len(funct["meta"]["returntype"]) > 0:
        model_doc["html"]["header"] += ": " + documentation_helpers.span_wrap(
            funct["meta"]["returntype"], "storage.type"
        )

    model_doc["html"]["arguments"] = ""
    model_doc["html"]["body"] = ""
    description_args = []

    if len(funct["meta"]["parameters"]) > 0:
        for index, arg in enumerate(funct["meta"]["parameters"]):

            if function_call_params.named_params:
                active_name = (
                    function_call_params.params[function_call_params.current_index][0]
                    or ""
                )
                is_active = active_name.lower() == arg["name"].lower()
            else:
                is_active = index == function_call_params.current_index

            if is_active:
                model_doc["html"]["body"] += (
                    "type: "
                    + documentation_helpers.span_wrap(
                        (arg["type"] if arg["type"] else "any"), "storage.type"
                    )
                    + "<br>"
                )
                model_doc["html"]["body"] += "required: " + (
                    "true<br>" if arg["required"] else "false<br>"
                )
                if arg["default"]:
                    model_doc["html"]["body"] += "default: " + arg["default"] + "<br>"
                if "hint" in arg and arg["hint"]:
                    model_doc["html"]["body"] += "<p>" + arg["hint"] + "</p>"

                description_args.append(
                    '<span class="active">' + arg["name"] + "</span>"
                )
            elif arg["required"]:
                description_args.append(
                    '<span class="required">' + arg["name"] + "</span>"
                )
            else:
                description_args.append(
                    '<span class="optional">' + arg["name"] + "</span>"
                )

        model_doc["html"]["arguments"] = "(" + ", ".join(description_args) + ")"

    return model_doc


def parse_functions(file_path, metadata):
    result = {}
    constructor = metadata["initmethod"].lower() if metadata["initmethod"] else "init"
    functions = metadata["functions"]
    function_file_map = metadata["function_file_map"]
    public_functions = [
        (functions[key], function_file_map[key])
        for key in sorted(functions)
        if key != constructor and is_public_function(functions[key])
    ]
    private_functions = [
        (functions[key], function_file_map[key])
        for key in sorted(functions)
        if key != constructor and not is_public_function(functions[key])
    ]
    result["public"] = [
        parse_function(function, funct_file_path, file_path)
        for function, funct_file_path in public_functions
    ]
    result["private"] = [
        parse_function(function, funct_file_path, file_path)
        for function, funct_file_path in private_functions
    ]
    if constructor in functions:
        result["constructor"] = parse_function(
            functions[constructor], function_file_map[constructor], file_path
        )
    return result


def is_public_function(function):
    if function["meta"]["access"] and function["meta"]["access"] == "private":
        return False
    return True


def parse_function(function, funct_file_path, file_path):
    header = '<a class="plain-link" href="' + function["name"] + '">'
    header += (
        documentation_helpers.span_wrap(function["name"], "entity.name.function")
        + "("
        + ("..." if function["meta"]["parameters"] else "")
        + ")"
    )
    if function["meta"]["returntype"]:
        header += ": " + documentation_helpers.span_wrap(
            function["meta"]["returntype"], "storage.type"
        )
    header += "</a>"

    body = ""
    if funct_file_path != file_path:
        body += " <small><em>(from " + funct_file_path.split("/")[-1] + ")</em></small>"
    if "hint" in function["meta"]:
        body += '<div class="doc-box">' + function["meta"]["hint"] + "</div>"

    arg_strings = []
    for arg in function["meta"]["parameters"]:
        arg_string = documentation_helpers.param_header(arg)
        if arg["default"]:
            arg_string += "<br>Default: " + arg["default"]
        if "hint" in arg and arg["hint"]:
            arg_string += "<div>" + arg["hint"] + "</div>"
        arg_strings.append(arg_string)

    if len(arg_strings) > 0:
        body += "<ul><li>" + "</li><li>".join(arg_strings) + "</li></ul>"

    return header, body


def parse_properties(file_path, metadata):
    properties = metadata["properties"]
    property_file_map = metadata["property_file_map"]
    sorted_properties = [
        (properties[key], property_file_map[key]) for key in sorted(properties)
    ]
    return [
        parse_property(prop, prop_file_path, file_path)
        for prop, prop_file_path in sorted_properties
    ]


def parse_property(prop, prop_file_path, file_path):
    header = (
        "<strong>"
        + prop["name"]
        + ": "
        + documentation_helpers.span_wrap(prop["meta"]["type"], "storage.type")
        + "</strong>"
    )
    if prop_file_path != file_path:
        header += (
            " <small><em>(from " + prop_file_path.split("/")[-1] + ")</em></small>"
        )

    body = ""
    accessors = [key for key in ["setter", "getter"] if prop["meta"][key]]
    if accessors:
        body += (
            "<small><strong>accessors</strong>: <em>"
            + ", ".join(accessors)
            + "</em></small>"
        )
    if "inject" in prop["meta"] and prop["meta"]["inject"]:
        body += "inject: " + prop["meta"]["inject"]
    return header, body


def get_function_region(view, function_name):
    functions = view.find_by_selector("entity.name.function -meta.function.body")
    for funct_region in functions:
        if view.substr(funct_region).lower() == function_name:
            pt = funct_region.begin()
            break
    else:
        return None

    if view.match_selector(pt, "meta.function.cfml"):
        # tag function
        decl = utils.get_scope_region_containing_point(view, pt, "meta.function.cfml")
        body = utils.get_scope_region_containing_point(
            view, decl.end() + 1, "meta.function.body.tag.cfml"
        )
        end = utils.get_scope_region_containing_point(
            view, body.end() + 1, "meta.tag.cfml"
        )
        return sublime.Region(decl.begin(), end.end())
    else:
        # script function
        decl = utils.get_scope_region_containing_point(
            view, pt, "meta.function.declaration.cfml"
        )
        body = utils.get_scope_region_containing_point(
            view, decl.end() + 1, "meta.function.body.cfml"
        )
        return sublime.Region(decl.begin(), body.end())
