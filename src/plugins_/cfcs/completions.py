from . import cfcs


def get_dot_completions(cfml_view):
    if not cfml_view.project_name or len(cfml_view.dot_context) == 0:
        return None
    # check for known cfc name
    cfc_name, cfc_name_region = cfcs.search_dot_context_for_cfc(
        cfml_view.project_name, cfml_view.dot_context
    )
    if cfc_name:
        return cfml_view.CompletionList(
            cfcs.get_cfc_completions(cfml_view.project_name, cfc_name), 1, True
        )

    # also check for getter being used to access property
    symbol = cfml_view.dot_context[-1]
    if symbol.is_function and symbol.name.startswith("get"):
        if cfcs.has_cfc(cfml_view.project_name, symbol.name[3:]):
            return cfml_view.CompletionList(
                cfcs.get_cfc_completions(cfml_view.project_name, symbol.name[3:]),
                1,
                True,
            )

    return None
