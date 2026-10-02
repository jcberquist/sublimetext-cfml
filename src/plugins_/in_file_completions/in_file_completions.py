import sublime
from ... import utils, component_index


def get_script_completions(cfml_view):
    completions = component_index.build_file_completions(cfml_view.view_metadata)[
        utils.get_setting("cfml_cfc_completions")
    ]
    completions = [
        component_index.to_completion_item(completion)
        for completion in completions["functions"]
    ]
    if len(completions) > 0:
        return cfml_view.CompletionList(completions)
    return None


def get_dot_completions(cfml_view):
    if len(cfml_view.dot_context) == 0:
        return None

    for symbol in cfml_view.dot_context:
        if not symbol.is_function:
            if symbol.name == "this":
                completions = component_index.build_file_completions(
                    cfml_view.view_metadata
                )[utils.get_setting("cfml_cfc_completions")]
                completions = [
                    component_index.to_completion_item(completion)
                    for completion in completions["functions"]
                ]
                return cfml_view.CompletionList(completions)

            if len(cfml_view.dot_context) == 1 and symbol.name == "arguments":
                current_function_body = utils.get_current_function_body(
                    cfml_view.view, cfml_view.position, component_method=False
                )
                if current_function_body:
                    function = cfml_view.get_function(current_function_body.begin() - 1)
                    meta = cfml_view.get_string_metadata(
                        cfml_view.view.substr(function[2]) + "{}"
                    )
                    if "functions" in meta and function[0] in meta["functions"]:
                        args = meta["functions"][function[0]]["meta"]["parameters"]
                        completions = [
                            sublime.CompletionItem(
                                arg["name"],
                                "arguments",
                                kind=(sublime.KIND_ID_VARIABLE, "a", "argument"),
                            )
                            for arg in args
                        ]
                        return cfml_view.CompletionList(completions)

            if (
                symbol.name == "super"
                and cfml_view.project_name
                and cfml_view.view_metadata["extends"]
            ):
                comp = component_index.component_index.get_completions_by_dot_path(
                    cfml_view.project_name, cfml_view.view_metadata["extends"]
                )

                if not comp and cfml_view.file_path:
                    extends_file_path = component_index.component_index.resolve_path(
                        cfml_view.project_name,
                        cfml_view.file_path,
                        cfml_view.view_metadata["extends"],
                    )
                    comp = component_index.component_index.get_completions_by_file_path(
                        cfml_view.project_name, extends_file_path
                    )

                if comp:
                    completions = [
                        component_index.to_completion_item(completion)
                        for completion in comp["functions"]
                    ]
                    return cfml_view.CompletionList(completions)

    return None
