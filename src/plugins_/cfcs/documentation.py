import sublime
from ...component_index import component_index
from ... import utils
from . import cfcs


def get_inline_documentation(cfml_view, doc_type):
    if not cfml_view.project_name:
        return None

    cfc_info, metadata, function_name, regions = find_cfc(cfml_view)

    if cfc_info:
        if function_name:
            doc, callback = component_index.get_method_documentation(
                cfml_view.view,
                cfml_view.project_name,
                cfc_info["file_path"],
                function_name,
                cfc_info["name"],
                metadata["functions"][function_name]["name"],
            )
        else:
            doc, callback = component_index.get_documentation(
                cfml_view.view,
                cfml_view.project_name,
                cfc_info["file_path"],
                cfc_info["name"],
            )
        return cfml_view.Documentation(regions, doc, callback, 2)

    return None


def get_method_preview(cfml_view):
    if not cfml_view.project_name:
        return None

    cfc_info, metadata, function_name, regions = find_cfc(cfml_view)

    if cfc_info and function_name:
        doc, callback = component_index.get_method_preview(
            cfml_view.view, cfml_view.project_name, cfc_info["file_path"], function_name
        )
        return cfml_view.MethodPreview(regions, doc, callback, 2)

    return None


def get_goto_cfml_file(cfml_view):
    if not cfml_view.project_name:
        return None

    cfc_info, metadata, function_name, regions = find_cfc(cfml_view)

    if cfc_info:
        if function_name:
            return cfml_view.GotoCfmlFile(
                cfc_info["file_path"], metadata["functions"][function_name]["name"]
            )
        else:
            return cfml_view.GotoCfmlFile(cfc_info["file_path"], None)

    return None


def get_completions_doc(cfml_view):
    if (
        not cfml_view.project_name
        or not cfml_view.function_call_params
        or not cfml_view.function_call_params.method
    ):
        return None

    symbol_name, symbol_region = cfcs.search_dot_context_for_cfc(
        cfml_view.project_name, cfml_view.function_call_params.dot_context
    )
    # also check for getter being used to access cfc
    if not symbol_name and len(cfml_view.function_call_params.dot_context):
        symbol = cfml_view.function_call_params.dot_context[-1]
        if (
            symbol.is_function
            and symbol.name.startswith("get")
            and cfcs.has_cfc(cfml_view.project_name, symbol.name[3:])
        ):
            symbol_name = symbol.name[3:]

    if symbol_name:
        cfc_info = cfcs.get_cfc_info(cfml_view.project_name, symbol_name)
        metadata = cfcs.get_cfc_metadata(cfml_view.project_name, symbol_name)
        if cfml_view.function_call_params.function_name in metadata["functions"]:
            doc, callback = component_index.get_function_call_params_doc(
                cfml_view.project_name,
                cfc_info["file_path"],
                cfml_view.function_call_params,
                cfc_info["name"],
                metadata["functions"][cfml_view.function_call_params.function_name][
                    "name"
                ],
            )
            return cfml_view.CompletionDoc(None, doc, callback)

    return None


def find_cfc(cfml_view):
    if cfml_view.view.match_selector(cfml_view.position, "meta.function-call.method"):
        function_name, function_name_region, function_args_region = cfml_view.get_function_call(
            cfml_view.position
        )
        region = sublime.Region(
            function_name_region.begin(), function_args_region.end()
        )
        if cfml_view.view.substr(function_name_region.begin() - 1) == ".":
            dot_context = cfml_view.get_dot_context(function_name_region.begin() - 1)
            # check for known cfc name
            symbol_name, symbol_region = cfcs.search_dot_context_for_cfc(
                cfml_view.project_name, dot_context
            )
            # also check for getter being used to access cfc
            if not symbol_name and len(dot_context):
                symbol = dot_context[-1]
                if (
                    symbol.is_function
                    and symbol.name.startswith("get")
                    and cfcs.has_cfc(cfml_view.project_name, symbol.name[3:])
                ):
                    symbol_name = symbol.name[3:]
                    symbol_region = symbol.name_region

            if symbol_name:
                cfc_info = cfcs.get_cfc_info(cfml_view.project_name, symbol_name)
                metadata = cfcs.get_cfc_metadata(cfml_view.project_name, symbol_name)
                if function_name in metadata["functions"]:
                    return cfc_info, metadata, function_name, [region, symbol_region]

    # check for cfc
    cfc_name = None
    check_position = cfml_view.position
    if cfml_view.view.match_selector(cfml_view.position, "punctuation.accessor.cfml"):
        check_position = cfml_view.position + 1
    if cfml_view.view.match_selector(
        check_position, "variable.other, meta.property.cfml"
    ):
        # we need to find the whole dot context now in order to search for variable names that contain dots
        dot_context = get_dot_context(cfml_view, check_position)
        cfc_name, cfc_name_region = cfcs.search_dot_context_for_cfc(
            cfml_view.project_name, dot_context
        )
        if cfc_name and not cfc_name_region.contains(cfml_view.position):
            cfc_name = None
    elif cfml_view.view.match_selector(
        cfml_view.position, "meta.tag.property.name.cfml"
    ):
        cfc_name_region = cfml_view.view.word(cfml_view.position)
        cfc_name = cfml_view.view.substr(cfc_name_region).lower()
    elif cfml_view.view.match_selector(
        cfml_view.position, "meta.function-call.cfml variable.function.cfml"
    ):
        cfc_name_region = cfml_view.view.word(cfml_view.position)
        var_name = cfml_view.view.substr(cfc_name_region).lower()
        if var_name.startswith("get"):
            cfc_name = var_name[3:]

    if cfc_name and cfcs.has_cfc(cfml_view.project_name, cfc_name):
        metadata = cfcs.get_cfc_metadata(cfml_view.project_name, cfc_name)
        cfc_info = cfcs.get_cfc_info(cfml_view.project_name, cfc_name)
        return cfc_info, metadata, None, [cfc_name_region]

    return None, None, None, None


def get_dot_context(cfml_view, position):
    current_element = cfml_view.view.word(position)
    next_pt = utils.get_next_character(cfml_view.view, current_element.end())

    if cfml_view.view.match_selector(
        next_pt, "punctuation.accessor.cfml"
    ) and cfml_view.view.match_selector(
        next_pt + 1, "variable.other, meta.property.cfml"
    ):
        return get_dot_context(cfml_view, next_pt + 1)

    dot_context = [
        utils.Symbol(
            cfml_view.view.substr(current_element), False, None, None, current_element
        )
    ]
    dot_context.extend(cfml_view.get_dot_context(current_element.begin() - 1))
    return dot_context
