import sublime
import json
from ... import utils


SIDE_COLOR = "color(var(--greenish) blend(var(--background) 60%))"


fw1 = {"settings": {}, "settings_docs": {}, "methods": {}, "methods_docs": {}}


def load():
    global fw1
    for key in fw1:
        data = load_json_data(key)
        if key == "settings":
            data = {k: make_setting_completions(k, data[k]) for k in data}
        elif key == "methods":
            data["calls"] = [
                (key + "\tframework.one", key.split("(")[0] + data["calls"][key])
                for key in sorted(data["calls"].keys())
            ]
            data["definitions"] = [
                (key + "\tframework.one", key.split("(")[0] + data["definitions"][key])
                for key in sorted(data["definitions"].keys())
            ]
            data["renderdata"] = [
                (key + "\trenderData()", key.split("(")[0] + data["renderdata"][key])
                for key in sorted(data["renderdata"].keys())
            ]
        fw1[key] = data


def load_json_data(filename):
    json_data = sublime.load_resource(
        "Packages/"
        + utils.get_plugin_name()
        + "/src/plugins_/fw1/json/"
        + filename
        + ".json"
    )
    return json.loads(json_data)


def make_setting_completions(prefix, source_list):
    return [(key + "\t" + prefix, key) for key in sorted(source_list)]


def get_setting(view, setting_key):
    if (
        view.window().project_file_name()
        and setting_key in view.window().project_data()
    ):
        return view.window().project_data()[setting_key]
    package_settings = sublime.load_settings("cfml_package.sublime-settings")
    return package_settings.get(setting_key)


def extends_fw1(cfml_view):
    if cfml_view.view_metadata["extends"]:
        return cfml_view.view_metadata["extends"] == "framework.one"
    return False


def get_file_type(view):
    if not view.file_name():
        return ""
    file_path = view.file_name().replace("\\", "/").lower()
    for file_type in ["view", "layout", "controller"]:
        for folder in get_setting(view, "fw1_" + file_type + "_folders"):
            if "/" + folder in file_path:
                return file_type
    return ""


def get_dot_completions(cfml_view):
    if (
        not get_setting(cfml_view.view, "fw1_enabled")
        or len(cfml_view.dot_context) == 0
    ):
        return None

    if extends_fw1(cfml_view):
        if cfml_view.dot_context[-1].name == "variables":
            key = ".".join([symbol.name for symbol in reversed(cfml_view.dot_context)])
            if key in fw1["settings"]:
                return cfml_view.CompletionList(fw1["settings"][key], 0, False)
        if cfml_view.dot_context[-1].name in ["renderdata", "renderer"]:
            return cfml_view.CompletionList(fw1["methods"]["renderdata"], 0, False)

    if get_file_type(cfml_view.view) == "controller":
        if len(cfml_view.dot_context) > 1 and cfml_view.dot_context[-2].name in [
            "renderdata",
            "renderer",
        ]:
            return cfml_view.CompletionList(fw1["methods"]["renderdata"], 0, False)
        if cfml_view.dot_context[-1].name in ["fw", "framework"]:
            return cfml_view.CompletionList(fw1["methods"]["calls"], 0, False)

    return None


def get_script_completions(cfml_view):
    if not get_setting(cfml_view.view, "fw1_enabled"):
        return None

    if extends_fw1(cfml_view):
        if cfml_view.view.match_selector(
            cfml_view.position,
            "meta.class.body.cfml -meta.function.body -meta.struct-literal",
        ):
            return cfml_view.CompletionList(fw1["methods"]["definitions"], 0, False)

        key = cfml_view.get_struct_var_assignment(cfml_view.position)

        if key and key in fw1["settings"]:
            return cfml_view.CompletionList(fw1["settings"][key], 0, False)

        return cfml_view.CompletionList(fw1["methods"]["calls"], 0, False)

    if get_file_type(cfml_view.view) in ["view", "layout"]:
        return cfml_view.CompletionList(fw1["methods"]["calls"], 0, False)

    return None


def get_inline_documentation(cfml_view, doc_type):
    if not get_setting(cfml_view.view, "fw1_enabled"):
        return None

    view_extends_fw1 = extends_fw1(cfml_view)
    view_file_type = get_file_type(cfml_view.view)

    # settings
    context = []
    word_region = cfml_view.view.word(cfml_view.position)

    if view_extends_fw1 and cfml_view.view.match_selector(
        cfml_view.position, "meta.property"
    ):
        context = cfml_view.get_dot_context(word_region.begin() - 1)

    if view_extends_fw1 and cfml_view.view.match_selector(
        cfml_view.position, "meta.class.body.cfml meta.struct-literal.cfml"
    ):
        context = cfml_view.get_struct_context(cfml_view.position)

    if len(context) > 0:
        key = ".".join([symbol.name for symbol in reversed(context)])
        if cfml_view.view.match_selector(
            cfml_view.position, "meta.property,meta.struct-literal.key,variable.other"
        ):
            key += "." + cfml_view.view.substr(word_region).lower()
        if key in fw1["settings_docs"]:
            return cfml_view.Documentation(
                [word_region],
                get_documentation(key, fw1["settings_docs"][key]),
                None,
                2,
            )
        parent_key = ".".join(key.split(".")[:-1])
        if parent_key in fw1["settings_docs"]:
            return cfml_view.Documentation(
                [context[0].name_region, word_region],
                get_documentation(parent_key, fw1["settings_docs"][parent_key]),
                None,
                2,
            )

    # methods
    if view_extends_fw1 and cfml_view.view.match_selector(
        cfml_view.position, "meta.function.declaration.cfml"
    ):
        function_name, function_name_region, function_region = cfml_view.get_function(
            cfml_view.position
        )
        region = sublime.Region(function_name_region.begin(), function_region.end())
        if function_name in fw1["methods_docs"]:
            return cfml_view.Documentation(
                [region],
                get_documentation(function_name, fw1["methods_docs"][function_name]),
                None,
                2,
            )

    if view_extends_fw1 or view_file_type in ["view", "layout"]:
        if cfml_view.view.match_selector(cfml_view.position, "meta.function-call"):
            function_name, function_name_region, function_args_region = cfml_view.get_function_call(
                cfml_view.position
            )
            region = sublime.Region(
                function_name_region.begin(), function_args_region.end()
            )
            if function_name in fw1["methods_docs"]:
                return cfml_view.Documentation(
                    [region],
                    get_documentation(
                        function_name, fw1["methods_docs"][function_name]
                    ),
                    None,
                    2,
                )

    if view_file_type == "controller" and cfml_view.view.match_selector(
        cfml_view.position, "meta.function-call.method"
    ):
        function_name, function_name_region, function_args_region = cfml_view.get_function_call(
            cfml_view.position
        )
        region = sublime.Region(
            function_name_region.begin(), function_args_region.end()
        )
        if cfml_view.view.substr(function_name_region.begin() - 1) == ".":
            dot_context = utils.get_dot_context(
                cfml_view.view, function_name_region.begin() - 1
            )
            if (
                dot_context[-1].name in ["fw", "framework"]
                and function_name in fw1["methods_docs"]
            ):
                return cfml_view.Documentation(
                    [region],
                    get_documentation(
                        function_name, fw1["methods_docs"][function_name]
                    ),
                    None,
                    2,
                )

    return None


def get_documentation(key, metadata):
    fw1_doc = {"side_color": SIDE_COLOR, "html": {}}
    fw1_doc["html"]["header"] = metadata["header"]
    fw1_doc["html"]["body"] = metadata["body"]
    fw1_doc["html"]["links"] = metadata["links"]
    return fw1_doc
