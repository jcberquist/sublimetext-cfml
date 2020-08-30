import sublime
import json
from ... import utils


SIDE_COLOR = "color(#336B81 blend(var(--background) 60%))"


testbox = {"completions": {}, "documentation": {}}


def _plugin_loaded():
    sublime.set_timeout_async(load)


def load():
    global testbox

    completions_data = load_json_data("completions")
    for key in completions_data:
        cfc = key.split(".").pop().capitalize()
        if cfc == "Basespec":
            cfc = "BaseSpec"
        testbox["completions"][key] = [
            (comp_key + "\t" + "TestBox " + cfc, completions_data[key][comp_key])
            for comp_key in sorted(completions_data[key].keys())
        ]
        if key == "expectation":
            negated_completions = [
                (
                    negate_string(comp_key) + "\t" + cfc,
                    negate_string(completions_data[key][comp_key]),
                )
                for comp_key in sorted(completions_data[key].keys())
            ]
            testbox["completions"][key].extend(negated_completions)

    testbox["documentation"] = load_json_data("documentation")


def load_json_data(filename):
    json_data = sublime.load_resource(
        "Packages/"
        + utils.get_plugin_name()
        + "/src/plugins_/testbox/json/"
        + filename
        + ".json"
    )
    return json.loads(json_data)


def negate_string(string_to_negate):
    return "not" + string_to_negate[0].upper() + string_to_negate[1:]


def get_setting(view, setting_key):
    if (
        view.window().project_file_name()
        and setting_key in view.window().project_data()
    ):
        return view.window().project_data()[setting_key]
    package_settings = sublime.load_settings("cfml_package.sublime-settings")
    return package_settings.get(setting_key)


def extends_testbox(cfml_view):
    if cfml_view.view_metadata["extends"]:
        return cfml_view.view_metadata["extends"].lower() == "testbox.system.basespec"
    return False


def is_testbox_file(cfml_view):
    if extends_testbox(cfml_view):
        return True

    if not cfml_view.file_name:
        return False

    for folder in get_setting(cfml_view.view, "testbox_folders"):
        if "/" + folder in cfml_view.file_path:
            return True
    return False


def get_dot_completions(cfml_view):
    if not get_setting(cfml_view.view, "testbox_enabled"):
        return None

    # expectations
    if (
        is_testbox_file(cfml_view)
        and len(cfml_view.dot_context) > 0
        and cfml_view.dot_context[-1].name == "expect"
    ):
        return cfml_view.CompletionList(testbox["completions"]["expectation"], 0, False)

    # assertions
    if (
        is_testbox_file(cfml_view)
        and len(cfml_view.dot_context) == 1
        and cfml_view.dot_context[-1].name == "assert"
    ):
        return cfml_view.CompletionList(testbox["completions"]["assertion"], 0, False)

    return None


def get_script_completions(cfml_view):
    if not get_setting(cfml_view.view, "testbox_enabled"):
        return None

    if is_testbox_file(cfml_view) and cfml_view.view.match_selector(
        cfml_view.position, "meta.class.body.cfml"
    ):
        return cfml_view.CompletionList(testbox["completions"]["basespec"], 0, False)

    return None


def get_inline_documentation(cfml_view, doc_type):
    if not get_setting(cfml_view.view, "testbox_enabled") or not is_testbox_file(
        cfml_view
    ):
        return None

    if cfml_view.view.match_selector(
        cfml_view.position, "meta.function-call.method.cfml"
    ):
        function_name, function_name_region, function_args_region = utils.get_function_call(
            cfml_view.view, cfml_view.position
        )
        region = sublime.Region(
            function_name_region.begin(), function_args_region.end()
        )
        if doc_type == "hover_doc" and not function_name_region.contains(
            cfml_view.position
        ):
            return None
        if cfml_view.view.substr(function_name_region.begin() - 1) == ".":
            dot_context = cfml_view.get_dot_context(function_name_region.begin() - 1)
            if dot_context[-1].name == "expect":
                if function_name in testbox["documentation"]["expectation"]:
                    doc = get_documentation(
                        function_name,
                        testbox["documentation"]["expectation"][function_name],
                    )
                    return cfml_view.Documentation(
                        [dot_context[-1].name_region, region], doc, None, 2
                    )
                if (
                    len(function_name) > 3
                    and function_name[:3] == "not"
                    and function_name[3:] in testbox["documentation"]["expectation"]
                ):
                    doc = testbox["documentation"]["expectation"][function_name[3:]]
                    return cfml_view.Documentation(
                        [dot_context[-1].name_region, region],
                        get_documentation(function_name, doc, True),
                        None,
                        2,
                    )
            if (
                dot_context[-1].name == "assert"
                and function_name in testbox["documentation"]["assertion"]
            ):
                doc = get_documentation(
                    function_name, testbox["documentation"]["assertion"][function_name]
                )
                return cfml_view.Documentation(
                    [dot_context[-1].name_region, region], doc, None, 2
                )

    if cfml_view.view.match_selector(cfml_view.position, "meta.function-call.cfml"):
        function_name, function_name_region, function_args_region = utils.get_function_call(
            cfml_view.view, cfml_view.position
        )
        region = sublime.Region(
            function_name_region.begin(), function_args_region.end()
        )
        if doc_type == "hover_doc" and not function_name_region.contains(
            cfml_view.position
        ):
            return None
        if function_name in testbox["documentation"]["basespec"]:
            doc = get_documentation(
                function_name, testbox["documentation"]["basespec"][function_name]
            )
            return cfml_view.Documentation([region], doc, None, 2)

    return None


def get_documentation(key, metadata, negated=False):
    testbox_doc = {"side_color": SIDE_COLOR, "html": {}}
    testbox_doc["html"]["header"] = metadata["header"]
    testbox_doc["html"]["body"] = metadata["body"]
    testbox_doc["html"]["links"] = metadata["links"]

    if negated:
        testbox_doc["html"]["header"] += " (negated)"
    return testbox_doc
