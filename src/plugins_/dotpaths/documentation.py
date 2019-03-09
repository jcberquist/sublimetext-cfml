from functools import partial
from ... import documentation_helpers
from ...component_index import component_index
from . import cfc_utils


SIDE_COLOR = "color(var(--bluish) blend(var(--background) 60%))"


def get_inline_documentation(cfml_view, doc_type):
    if not cfml_view.project_name:
        return None

    cfc_path, file_path, dot_path, function_name, regions = cfc_utils.find_cfc(
        cfml_view, cfml_view.position
    )

    if file_path:
        if dot_path:
            if function_name:
                metadata = component_index.get_extended_metadata_by_file_path(
                    cfml_view.project_name, file_path
                )
                if function_name in metadata["functions"]:
                    doc, callback = component_index.get_method_documentation(
                        cfml_view.view,
                        cfml_view.project_name,
                        file_path,
                        function_name,
                        dot_path.split(".").pop(),
                        metadata["functions"][function_name]["name"],
                    )
                    return cfml_view.Documentation(regions, doc, callback, 2)

            doc, callback = component_index.get_documentation(
                cfml_view.view, cfml_view.project_name, file_path, dot_path
            )
            return cfml_view.Documentation(regions, doc, callback, 2)

        doc, callback = get_documentation(
            cfml_view.view,
            file_path,
            documentation_helpers.span_wrap(cfc_path, "entity.name.class"),
        )
        return cfml_view.Documentation(regions, doc, callback, 2)

    return None


def get_method_preview(cfml_view):
    if not cfml_view.project_name:
        return None

    cfc_path, file_path, dot_path, function_name, regions = cfc_utils.find_cfc(
        cfml_view, cfml_view.position
    )

    if file_path and dot_path and function_name:
        doc, callback = component_index.get_method_preview(
            cfml_view.view, cfml_view.project_name, file_path, function_name
        )
        return cfml_view.MethodPreview(regions, doc, callback, 2)

    return None


def get_goto_cfml_file(cfml_view):
    if not cfml_view.project_name:
        return None

    cfc_path, file_path, dot_path, function_name, region = cfc_utils.find_cfc(
        cfml_view, cfml_view.position
    )

    if file_path:
        if function_name:
            metadata = component_index.get_extended_metadata_by_file_path(
                cfml_view.project_name, file_path
            )
            if function_name in metadata["functions"]:
                return cfml_view.GotoCfmlFile(
                    metadata["function_file_map"][function_name],
                    metadata["functions"][function_name]["name"],
                )
        else:
            return cfml_view.GotoCfmlFile(file_path, None)

    return None


def get_completions_doc(cfml_view):
    if (
        not cfml_view.project_name
        or not cfml_view.function_call_params
        or not cfml_view.function_call_params.method
    ):
        return None

    if len(cfml_view.function_call_params.dot_context) != 1:
        return None

    start_pt = cfml_view.function_call_params.dot_context[0].name_region.begin()
    cfc_path, file_path, dot_path, temp_function_name, region = cfc_utils.find_cfc(
        cfml_view, start_pt
    )

    if file_path:
        function_name = cfml_view.function_call_params.function_name
        metadata = component_index.get_extended_metadata_by_file_path(
            cfml_view.project_name, file_path
        )
        if (
            metadata
            and cfml_view.function_call_params.function_name in metadata["functions"]
        ):
            doc, callback = component_index.get_function_call_params_doc(
                cfml_view.project_name,
                file_path,
                cfml_view.function_call_params,
                dot_path.split(".").pop(),
                metadata["functions"][function_name]["name"],
            )
            return cfml_view.CompletionDoc(None, doc, callback)

    return None


def on_navigate(view, file_path, href):
    view.window().open_file(file_path)


def get_documentation(view, file_path, header):
    cfc_doc = {"side_color": SIDE_COLOR, "html": {}}
    cfc_doc["html"]["links"] = []

    cfc_doc["html"]["header"] = header
    cfc_doc["html"][
        "body"
    ] = """
    <div class="path">
        <strong>path</strong>: <a href="__go_to_component">{}</a>
    </div>
    """.strip().format(
        file_path
    )

    callback = partial(on_navigate, view, file_path)
    return cfc_doc, callback
