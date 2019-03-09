import re
import sublime
from ...component_index import component_index
from ... import utils


entity_name_re = r"""
\(\s*["']([$_\w.]+)["']
"""
entity_name_re = re.compile(entity_name_re, re.I | re.X)

entityload_re = r"""
\(\s*["']([$_\w.]+)["'].*true\s*\)
"""
entityload_re = re.compile(entityload_re, re.I | re.X)


def get_entity_name(source_string, function_name):
    en = re.search(
        entityload_re if function_name == "entityload" else entity_name_re,
        source_string,
    )
    if en:
        return en.group(1).lower()
    return None


def is_possible_entity(dot_context):
    if dot_context[0].is_function:
        return False
    if len(dot_context) == 1:
        return True
    if len(dot_context) == 2 and dot_context[1].name == "variables":
        return True
    return False


def find_entity(cfml_view, position):
    """
    returns entity_name, function_name, regions
    """
    if cfml_view.view.match_selector(
        position, "meta.function-call.support.entity.cfml"
    ):
        function_name, function_region, args_region = cfml_view.get_function_call(
            position
        )
        region = sublime.Region(function_region.begin(), args_region.end())
        entity_name = get_entity_name(cfml_view.view.substr(args_region), function_name)
        return entity_name, None, [region]

    if cfml_view.view.match_selector(position, "meta.function-call.method"):
        function_name, function_name_region, function_args_region = cfml_view.get_function_call(
            position
        )
        funct_region = sublime.Region(
            function_name_region.begin(), function_args_region.end()
        )
        if cfml_view.view.substr(function_name_region.begin() - 1) == ".":
            dot_context = cfml_view.get_dot_context(function_name_region.begin() - 1)
            if len(dot_context):
                if cfml_view.view.match_selector(
                    dot_context[-1].name_region.begin(),
                    "meta.function-call.support.entity.cfml",
                ):
                    region = sublime.Region(
                        dot_context[-1].function_region.begin(),
                        dot_context[-1].args_region.end(),
                    )
                    entity_name = get_entity_name(
                        cfml_view.view.substr(dot_context[-1].args_region),
                        dot_context[-1].name,
                    )
                    return entity_name, function_name, [region, funct_region]

                if is_possible_entity(dot_context):
                    entity_name, temp, regions = find_entity_by_var_assignment(
                        cfml_view, position, dot_context[0].name
                    )
                    if regions:
                        regions.append(dot_context[0].name_region)
                        regions.append(funct_region)
                    return entity_name, function_name, regions

    if cfml_view.view.match_selector(position, "variable.other, meta.property.cfml"):
        var_region = cfml_view.view.word(position)
        dot_context = cfml_view.get_dot_context(var_region.begin() - 1)
        if len(dot_context) == 0 or (
            len(dot_context) == 1 and dot_context[0].name == "variables"
        ):
            entity_name, function_name, regions = find_entity_by_var_assignment(
                cfml_view, position, cfml_view.view.substr(var_region).lower()
            )
            if regions:
                regions.append(var_region)
            return entity_name, function_name, regions

    return None, None, None


def find_entity_by_var_assignment(cfml_view, position, var_name):
    empty_tuple = None, None, None

    if not utils.get_setting("instantiated_component_completions"):
        return empty_tuple

    var_assignment_region = cfml_view.find_variable_assignment(position, var_name)
    if not var_assignment_region:
        return empty_tuple

    if not cfml_view.view.match_selector(
        var_assignment_region.end(), "meta.function-call.support.entity.cfml"
    ):
        return empty_tuple

    entity_name, function_name, regions = find_entity(
        cfml_view, var_assignment_region.end()
    )

    if entity_name is None:
        return empty_tuple

    regions.append(var_assignment_region)
    next_pt = utils.get_next_character(cfml_view.view, regions[0].end())

    if cfml_view.view.substr(next_pt) != ".":
        return entity_name, function_name, regions

    # if next char is a `.`, try to determine if what follows is init method
    if not cfml_view.view.match_selector(next_pt + 1, "meta.function-call.method"):
        return empty_tuple

    function_name, function_name_region, function_args_region = cfml_view.get_function_call(
        next_pt + 1
    )

    if not function_name:
        return empty_tuple

    file_path = component_index.get_file_path_by_entity_name(
        cfml_view.project_name, entity_name
    )
    metadata = component_index.get_extended_metadata_by_file_path(
        cfml_view.project_name, file_path["file_path"]
    )

    if metadata["initmethod"] is None:
        if function_name != "init":
            return empty_tuple
    else:
        if metadata["initmethod"] != function_name:
            return empty_tuple

    next_pt = utils.get_next_character(cfml_view.view, function_args_region.end())

    if cfml_view.view.substr(next_pt) == ".":
        return empty_tuple

    return entity_name, function_name, regions
