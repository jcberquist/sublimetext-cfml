from .. import model_index
from . import entity_utils


def get_inline_documentation(cfml_view, doc_type):
    if not cfml_view.project_name:
        return None

    entity_name, function_name, regions = entity_utils.find_entity(cfml_view, cfml_view.position)

    if entity_name:
        file_path_info = model_index.get_file_path_by_entity_name(cfml_view.project_name, entity_name)
        if file_path_info is None:
            return None

        if function_name:
            metadata = model_index.get_extended_metadata_by_file_path(cfml_view.project_name, file_path_info["file_path"])
            if function_name in metadata["functions"]:
                header = file_path_info["entity_name"] + "." + metadata["functions"][function_name].name + "()"
                doc, callback = model_index.get_method_documentation(cfml_view.view, cfml_view.project_name, file_path_info["file_path"], function_name, header)
                return cfml_view.Documentation(regions, doc, callback, 2)
        doc, callback = model_index.get_documentation(cfml_view.view, cfml_view.project_name, file_path_info["file_path"], file_path_info["entity_name"])
        return cfml_view.Documentation(regions, doc, callback, 2)

    return None


def get_goto_cfml_file(cfml_view):
    if not cfml_view.project_name:
        return None

    entity_name, function_name, region = entity_utils.find_entity(cfml_view, cfml_view.position)

    if entity_name:
        file_path_info = model_index.get_file_path_by_entity_name(cfml_view.project_name, entity_name)
        if file_path_info is None:
            return None
        if function_name:
            metadata = model_index.get_extended_metadata_by_file_path(cfml_view.project_name, file_path_info["file_path"])
            if function_name in metadata["functions"]:
                return cfml_view.GotoCfmlFile(metadata["function_file_map"][function_name], metadata["functions"][function_name].name)
        else:
            return cfml_view.GotoCfmlFile(file_path_info["file_path"], None)

    return None


def get_completions_doc(cfml_view):
    if not cfml_view.project_name or not cfml_view.function_call_params or not cfml_view.function_call_params.method:
        return None

    if len(cfml_view.function_call_params.dot_context) > 1:
        return None

    start_pt = cfml_view.function_call_params.dot_context[0].name_region.begin()
    entity_name, temp_function_name, region = entity_utils.find_entity(cfml_view, start_pt)

    if entity_name:
        file_path_info = model_index.get_file_path_by_entity_name(cfml_view.project_name, entity_name)
        if file_path_info is None:
            return None
        function_name = cfml_view.function_call_params.function_name
        metadata = model_index.get_extended_metadata_by_file_path(cfml_view.project_name, file_path_info["file_path"])
        if cfml_view.function_call_params.function_name in metadata["functions"]:
            header = file_path_info["entity_name"] + "." + metadata["functions"][function_name].name + "()"
            doc, callback = model_index.get_function_call_params_doc(cfml_view.project_name, file_path_info["file_path"], cfml_view.function_call_params, header)
            return cfml_view.CompletionDoc(None, doc, callback)

    return None
