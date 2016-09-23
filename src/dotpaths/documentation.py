from functools import partial
from .. import model_index
from .. import utils
from . import cfc_utils

STYLES = {
    "side_color": "#4C9BB0",
    "header_color": "#306B7B",
    "header_bg_color": "#E4EEF1",
    "text_color": "#272B33"
}


def get_inline_documentation(cfml_view):
    if not cfml_view.project_name:
        return None

    cfc_path, file_path, dot_path, function_name, region = cfc_utils.find_cfc(cfml_view, cfml_view.position)

    if file_path:
        if dot_path:
            if function_name:
                metadata = model_index.get_extended_metadata_by_file_path(cfml_view.project_name, file_path)
                if function_name in metadata["functions"]:
                    header = dot_path.split(".").pop() + "." + metadata["functions"][function_name].name + "()"
                    doc, callback = model_index.get_method_documentation(cfml_view.view, cfml_view.project_name, file_path, function_name, header)
                    return cfml_view.Documentation(doc, callback, 2)
            doc, callback = model_index.get_documentation(cfml_view.view, cfml_view.project_name, file_path, dot_path)
            return cfml_view.Documentation(doc, callback, 2)
        doc, callback = get_documentation(cfml_view.view, file_path, cfc_path)
        return cfml_view.Documentation(doc, callback, 2)

    # check for assigned variable

    return None


def get_goto_cfml_file(cfml_view):
    if not cfml_view.project_name:
        return None

    cfc_path, file_path, dot_path, function_name, region = cfc_utils.find_cfc(cfml_view, cfml_view.position)

    if file_path:
        if function_name:
            metadata = model_index.get_extended_metadata_by_file_path(cfml_view.project_name, file_path)
            if function_name in metadata["functions"]:
                return cfml_view.GotoCfmlFile(metadata["function_file_map"][function_name], metadata["functions"][function_name].name)
        else:
            return cfml_view.GotoCfmlFile(file_path, None)

    return None


def get_completions_doc(cfml_view):
    if not cfml_view.project_name or not cfml_view.function_call_params or not cfml_view.function_call_params.method:
        return None

    if len(cfml_view.function_call_params.dot_context) > 1:
        return None

    start_pt = cfml_view.function_call_params.dot_context[0].name_region.begin()
    cfc_path, file_path, dot_path, temp_function_name, region = cfc_utils.find_cfc(cfml_view, start_pt)

    if file_path:
        function_name = cfml_view.function_call_params.function_name
        metadata = model_index.get_extended_metadata_by_file_path(cfml_view.project_name, file_path)
        if cfml_view.function_call_params.function_name in metadata["functions"]:
            header = dot_path.split(".").pop() + "." + metadata["functions"][function_name].name + "()"
            doc, callback = model_index.get_function_call_params_doc(cfml_view.project_name, file_path, cfml_view.function_call_params, header)
            return cfml_view.CompletionDoc(doc, callback)

    return None


def on_navigate(view, file_path, href):
    view.window().open_file(file_path)


def get_documentation(view, file_path, header):
    cfc_doc = dict(STYLES)
    cfc_doc["links"] = []

    cfc_doc["header"] = header
    cfc_doc["description"] = "<strong>path</strong>: <a class=\"alt-link\" href=\"__go_to_component\">" + file_path + "</a>"

    callback = partial(on_navigate, view, file_path)
    return cfc_doc, callback
