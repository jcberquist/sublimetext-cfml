from ... import utils, component_index


def get_script_completions(cfml_view):
    completions = component_index.build_file_completions(cfml_view.view_metadata)[
        utils.get_setting("cfml_cfc_completions")
    ]
    completions = [
        make_completion(completion, cfml_view.file_path)
        for completion in completions["functions"]
    ]
    if len(completions) > 0:
        return cfml_view.CompletionList(completions, 0, False)
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
                    make_completion(completion, cfml_view.file_path)
                    for completion in completions["functions"]
                ]
                return cfml_view.CompletionList(completions, 0, False)

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
                            (arg["name"] + "\targuments", arg["name"]) for arg in args
                        ]
                        return cfml_view.CompletionList(completions, 0, False)

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
                        (completion.key + "\t" + completion.hint, completion.content)
                        for completion in comp["functions"]
                    ]
                    return cfml_view.CompletionList(completions, 0, False)

    return None


def make_completion(comp, file_path):
    hint = "this"
    if len(comp.file_path) > 0 and comp.file_path != file_path:
        hint = comp.hint
    return (comp.key + "\t" + hint, comp.content)
