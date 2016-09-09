import sublime
from functools import partial
from .. import utils, model_index


SYNTAX_EXT = "sublime-syntax" if int(sublime.version()) >= 3092 else "tmLanguage"


def get_inline_documentation(cfml_view):
    extended_meta, function_name, header = get_function_info(cfml_view)

    if extended_meta:
        doc, callback = get_function_documentation(cfml_view.view, extended_meta, function_name, header)
        return cfml_view.Documentation(doc, callback, 2)

    extended_meta, file_path, header = get_cfc_info(cfml_view)
    if extended_meta:
        doc, callback = get_documentation(cfml_view.view, extended_meta, file_path, header)
        return cfml_view.Documentation(doc, callback, 2)

    return None


def get_goto_cfml_file(cfml_view):

    extended_meta, function_name, header = get_function_info(cfml_view)
    if extended_meta:
        return cfml_view.GotoCfmlFile(extended_meta["function_file_map"][function_name], extended_meta["functions"][function_name].name)

    extended_meta, file_path, header = get_cfc_info(cfml_view)
    if extended_meta:
        return cfml_view.GotoCfmlFile(file_path, None)

    return None


def get_function_info(cfml_view):
    if cfml_view.view.match_selector(cfml_view.position, "meta.function-call.cfml"):
        function_name, function_name_region, function_args_region = cfml_view.get_function_call(cfml_view.position)
        if function_name in cfml_view.view_metadata["functions"]:
            header = cfml_view.view_metadata["functions"][function_name].name + "()"
            return cfml_view.view_metadata, function_name, header

    if cfml_view.view.match_selector(cfml_view.position, "meta.function-call.method.cfml"):
        function_name, function_name_region, function_args_region = cfml_view.get_function_call(cfml_view.position)
        if cfml_view.view.substr(function_name_region.begin() - 1) == ".":
            dot_context = cfml_view.get_dot_context(function_name_region.begin() - 1)

            if dot_context[0].name == "this":
                if function_name in cfml_view.view_metadata["functions"]:
                    header = cfml_view.view_metadata["functions"][function_name].name + "()"
                    return cfml_view.view_metadata, function_name, header

            if dot_context[0].name == "super":
                file_path = cfml_view.file_path or ""
                extends_file_path = model_index.resolve_path(cfml_view.project_name, file_path, cfml_view.view_metadata["extends"])
                cfml_view.view_metadata = model_index.get_extended_metadata_by_file_path(cfml_view.project_name, extends_file_path)
                if cfml_view.view_metadata and function_name in cfml_view.view_metadata["functions"]:
                    header = cfml_view.view_metadata["functions"][function_name].name + "()"
                    return cfml_view.view_metadata, function_name, header

    return None, None, None


def get_cfc_info(cfml_view):
    file_path = cfml_view.file_path or ""

    if cfml_view.view.match_selector(cfml_view.position, "variable.language.this.cfml"):
        return cfml_view.view_metadata, file_path, "this"

    if cfml_view.view.match_selector(cfml_view.position, "variable.language.super.cfml"):
        extends_file_path = model_index.resolve_path(cfml_view.project_name, file_path, cfml_view.view_metadata["extends"])
        extended_meta = model_index.get_extended_metadata_by_file_path(cfml_view.project_name, extends_file_path)
        if extended_meta:
            return extended_meta, extends_file_path, cfml_view.view_metadata["extends"]

    return None, None, None


def on_navigate(view, file_path, function_file_map, href):

    if href == "__go_to_component":
        if len(file_path) > 2 and file_path[1] == ":":
            file_path = "/" + file_path[0] + file_path[2:]
        view.window().open_file(file_path)
    else:
        file_path = function_file_map[href.lower()]
        if len(file_path) > 2 and file_path[1] == ":":
            file_path = "/" + file_path[0] + file_path[2:]
        view.hide_popup()
        view.window().run_command('cfml_navigate_to_method', {"file_path": file_path, "href": href})


def get_documentation(view, extended_meta, file_path, header):
    model_doc = model_index.build_documentation(extended_meta, file_path, header)
    callback = partial(on_navigate, view, file_path, extended_meta["function_file_map"])
    return model_doc, callback


def get_function_documentation(view, extended_meta, function_name, header):
    function_file_path = extended_meta["function_file_map"][function_name]
    view_file_path = utils.normalize_path(view.file_name()) if view.file_name() else ""
    if len(function_file_path) > 0 and function_file_path != view_file_path:
        with open(function_file_path, "r", encoding="utf-8") as f:
            file_string = f.read()
        cfml_minihtml_view = view.window().create_output_panel("cfml_minihtml")
        cfml_minihtml_view.assign_syntax("Packages/" + utils.get_plugin_name() + "/syntaxes/cfml." + SYNTAX_EXT)
        cfml_minihtml_view.run_command("append", {"characters": file_string, "force": True, "scroll_to_end": True})
        model_doc = model_index.build_method_documentation(extended_meta, function_name, header, cfml_minihtml_view)
        view.window().destroy_output_panel("cfml_minihtml")
    else:
        model_doc = model_index.build_method_documentation(extended_meta, function_name, header, view)

    callback = partial(on_navigate, view, extended_meta["function_file_map"][function_name], extended_meta["function_file_map"])
    return model_doc, callback
