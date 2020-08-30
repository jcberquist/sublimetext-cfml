from ...component_index import component_index
from . import entity_utils


projects = {}


def build_project_entities(project_name):
    global projects
    entities = component_index.get_entities(project_name)
    completions = []
    for key in entities:
        completions.append(
            (entities[key]["entity_name"] + "\tentity", entities[key]["entity_name"])
        )
    projects[project_name] = completions


def get_script_completions(cfml_view):
    if not cfml_view.project_name or cfml_view.project_name not in projects:
        return None

    if cfml_view.view.match_selector(
        cfml_view.position,
        "meta.function-call.support.entity.cfml meta.function-call.parameters.support.cfml string.quoted",
    ):
        if is_entityname_param(cfml_view.function_call_params):
            completions = projects[cfml_view.project_name]
            if len(completions) > 0:
                return cfml_view.CompletionList(completions, 0, False)

    return None


def get_dot_completions(cfml_view):
    if not cfml_view.project_name or len(cfml_view.dot_context) == 0:
        return None

    entity_selector = "meta.function-call.support.entity.cfml"
    entity_methods = ["entitynew", "entityload", "entityloadbypk"]
    entity_name = None

    if cfml_view.dot_context[
        0
    ].name in entity_methods and cfml_view.view.match_selector(
        cfml_view.prefix_start - 2, entity_selector
    ):
        entity_name = entity_utils.get_entity_name(
            cfml_view.view.substr(cfml_view.dot_context[0].args_region),
            cfml_view.dot_context[0].name,
        )

    elif entity_utils.is_possible_entity(cfml_view.dot_context):
        entity_tuple = entity_utils.find_entity_by_var_assignment(
            cfml_view, cfml_view.prefix_start, cfml_view.dot_context[0].name
        )
        if entity_tuple[0] is not None:
            entity_name = entity_tuple[0]

    if entity_name:
        completions = get_completions_by_entity_name(
            cfml_view.project_name, entity_name
        )
        if completions:
            return cfml_view.CompletionList(completions, 0, False)

    return None


def is_entityname_param(function_call_params):
    if function_call_params.named_params:
        active_name = (
            function_call_params.params[function_call_params.current_index][0] or ""
        )
        return active_name.lower() == "entityname"

    return function_call_params.current_index == 0


def get_completions_by_entity_name(project_name, entity_name):
    comp = component_index.get_completions_by_entity_name(project_name, entity_name)

    if comp:
        filtered_completions = []
        for completion in comp["functions"]:
            if not completion.private:
                hint = "method" if completion.hint == "method" else entity_name
                filtered_completions.append(
                    (completion.key + "\t" + hint, completion.content)
                )
        return filtered_completions

    return None
