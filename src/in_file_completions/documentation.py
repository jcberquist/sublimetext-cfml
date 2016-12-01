import sublime
from functools import partial
from .. import utils, model_index


def get_inline_documentation(cfml_view, doc_type):
    extended_meta, function_name, header, regions = get_function_info(cfml_view, cfml_view.position)

    if extended_meta:
        doc, callback = get_function_documentation(cfml_view.view, cfml_view.project_name, extended_meta, function_name, header)
        return cfml_view.Documentation(regions, doc, callback, 2)

    extended_meta, file_path, header, regions = get_cfc_info(cfml_view, cfml_view.position)
    if extended_meta:
        doc, callback = get_documentation(cfml_view.view, extended_meta, file_path, header)
        return cfml_view.Documentation(regions, doc, callback, 2)

    return None


def get_goto_cfml_file(cfml_view):

    extended_meta, function_name, header, regions = get_function_info(cfml_view, cfml_view.position)
    if extended_meta:
        return cfml_view.GotoCfmlFile(extended_meta["function_file_map"][function_name], extended_meta["functions"][function_name].name)

    extended_meta, file_path, header, regions = get_cfc_info(cfml_view, cfml_view.position)
    if extended_meta:
        return cfml_view.GotoCfmlFile(file_path, None)

    return None


def get_completion_docs(cfml_view):
    if cfml_view.function_call_params and not cfml_view.function_call_params.support:
        header = get_function_call_params_header(cfml_view)

        if header:
            model_doc = model_index.build_function_call_params_doc(cfml_view.view_metadata, cfml_view.function_call_params, header)
            return cfml_view.CompletionDoc(None, model_doc, None)

    return None


def get_function_info(cfml_view, pt):
    if cfml_view.view.match_selector(pt, "meta.function-call.cfml"):
        function_name, function_name_region, function_args_region = cfml_view.get_function_call(pt)
        if function_name in cfml_view.view_metadata["functions"]:
            header = cfml_view.view_metadata["functions"][function_name].name + "()"
            region = sublime.Region(function_name_region.begin(), function_args_region.end())
            return cfml_view.view_metadata, function_name, header, [region]

    if cfml_view.view.match_selector(pt, "meta.function-call.method.cfml"):
        function_name, function_name_region, function_args_region = cfml_view.get_function_call(pt)
        region = sublime.Region(function_name_region.begin(), function_args_region.end())
        if cfml_view.view.substr(function_name_region.begin() - 1) == ".":
            dot_context = cfml_view.get_dot_context(function_name_region.begin() - 1)

            if dot_context[0].name == "this":
                if function_name in cfml_view.view_metadata["functions"]:
                    header = cfml_view.view_metadata["functions"][function_name].name + "()"
                    return cfml_view.view_metadata, function_name, header, [region, dot_context[0].name_region]

            if dot_context[0].name == "super":
                if cfml_view.view_metadata and function_name in cfml_view.view_metadata["functions"]:
                    header = cfml_view.view_metadata["functions"][function_name].name + "()"
                    return cfml_view.view_metadata, function_name, header, [region, dot_context[0].name_region]

    return None, None, None, None


def get_function_call_params_header(cfml_view):
    if not cfml_view.function_call_params.method:
        if cfml_view.function_call_params.function_name in cfml_view.view_metadata["functions"]:
            header = cfml_view.view_metadata["functions"][cfml_view.function_call_params.function_name].name + "()"
            return header
    else:
        if cfml_view.function_call_params.dot_context[0].name == "this":
            if cfml_view.function_call_params.function_name in cfml_view.view_metadata["functions"]:
                header = cfml_view.view_metadata["functions"][cfml_view.function_call_params.function_name].name + "()"
                return header

        if cfml_view.function_call_params.dot_context[0].name == "super":
            if cfml_view.view_metadata and cfml_view.function_call_params.function_name in cfml_view.view_metadata["functions"]:
                header = cfml_view.view_metadata["functions"][cfml_view.function_call_params.function_name].name + "()"
                return header

    return None


def get_cfc_info(cfml_view, pt):
    file_path = cfml_view.file_path or ""

    if cfml_view.view.match_selector(pt, "variable.language.this.cfml"):
        return cfml_view.view_metadata, file_path, "this", [cfml_view.view.word(pt)]

    if cfml_view.view.match_selector(pt, "variable.language.super.cfml"):
        extends_file_path = model_index.resolve_path(cfml_view.project_name, file_path, cfml_view.view_metadata["extends"])
        extended_meta = model_index.get_extended_metadata_by_file_path(cfml_view.project_name, extends_file_path)
        if extended_meta:
            return extended_meta, extends_file_path, cfml_view.view_metadata["extends"], [cfml_view.view.word(pt)]

    return None, None, None, None


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


def get_function_documentation(view, project_name, extended_meta, function_name, header):
    function_file_path = extended_meta["function_file_map"][function_name]
    view_file_path = utils.normalize_path(view.file_name()) if view.file_name() else ""
    if len(function_file_path) > 0 and function_file_path != view_file_path:
        model_doc, callback = model_index.get_method_documentation(view, project_name, function_file_path, function_name, header)
    else:
        function_preview = model_index.build_method_preview(view, function_name)
        model_doc = model_index.build_method_documentation(extended_meta, function_name, header, function_preview)
        callback = partial(on_navigate, view, extended_meta["function_file_map"][function_name], extended_meta["function_file_map"])

    return model_doc, callback
