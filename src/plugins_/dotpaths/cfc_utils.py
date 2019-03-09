import re
import sublime
from os.path import dirname
from ...component_index import component_index
from ... import utils


component_name_re = r"""
["']component["']\s*,\s*(?:class\s*=\s*)?["']([$_\w.]+)["']
"""
component_name_re = re.compile(component_name_re, re.I | re.X)

cfc_dot_path_re = re.compile(r"^[\w\-_][\w.\-_]+$")
component_selector = "meta.function-call.support.createcomponent.cfml"
constructor_selector = "meta.instance.constructor.cfml"


def get_component_name(source_string):
    cn = re.search(component_name_re, source_string)
    if cn:
        return cn.group(1)
    return None


def is_cfc_dot_path(source_string):
    dp = re.search(cfc_dot_path_re, source_string)
    if dp:
        return True
    return False


def is_possible_cfc_instance(dot_context):
    if dot_context[0].is_function:
        return False
    if len(dot_context) == 1:
        return True
    if len(dot_context) == 2 and dot_context[1].name == "variables":
        return True
    return False


def get_folder_cfc_path(cfml_view, cfc_path):
    folder_mapping = get_folder_mapping(cfml_view)
    if folder_mapping:
        folder_cfc_path = folder_mapping
        if len(cfc_path) > 0:
            folder_cfc_path += "." + cfc_path
        return folder_cfc_path
    return None


def get_folder_mapping(cfml_view):
    """
    Checks current file to see if it is inside of a mapped folder
    and returns the dot path to the file's containing folder.

    For example, if 'C:/projects/project/model/' is mapped to '/model',
    and the current file is 'C:/projects/project/model/services/myservice.cfc'
    then this function will return 'model.services'
    """
    if not cfml_view.file_path:
        return None
    mappings = component_index.get_project_data(cfml_view.project_name).get(
        "mappings", []
    )
    for mapping in mappings:
        normalized_mapping = utils.normalize_mapping(
            mapping, dirname(cfml_view.project_name)
        )
        if not cfml_view.file_path.startswith(normalized_mapping["path"]):
            continue
        mapped_path = normalized_mapping["mapping"] + cfml_view.file_path.replace(
            normalized_mapping["path"], ""
        )
        path_parts = mapped_path.split("/")[1:-1]
        dot_path = ".".join(path_parts)
        if len(dot_path) > 0:
            return dot_path
    return None


def find_cfc(cfml_view, position):
    """
    returns cfc_path, file_path, dot_path, function_name, regions
    """
    if cfml_view.view.match_selector(position, "entity.other.inherited-class.cfml"):
        r = utils.get_scope_region_containing_point(
            cfml_view.view, position, "entity.other.inherited-class.cfml"
        )
        cfc_path = cfml_view.view.substr(r)
        file_path, dot_path = get_cfc_file_info(cfml_view, cfc_path)
        return cfc_path, file_path, dot_path, None, [r]

    if cfml_view.view.match_selector(position, component_selector):
        r = utils.get_scope_region_containing_point(
            cfml_view.view, position, component_selector
        )
        cfc_path = get_component_name(cfml_view.view.substr(r))
        file_path, dot_path = get_cfc_file_info(cfml_view, cfc_path)
        return cfc_path, file_path, dot_path, None, [r]

    if cfml_view.view.match_selector(position, constructor_selector):
        r = utils.get_scope_region_containing_point(
            cfml_view.view, position, constructor_selector
        )
        cfc_path = cfml_view.view.substr(r)[4:].split("(")[0]
        file_path, dot_path = get_cfc_file_info(cfml_view, cfc_path)
        return cfc_path, file_path, dot_path, None, [r]

    if cfml_view.view.match_selector(
        position, "string.quoted.single.cfml, string.quoted.double.cfml"
    ):
        r = cfml_view.view.extract_scope(position)
        cfc_path = cfml_view.view.substr(r)
        if cfc_path[0] in ['"', "'"]:
            cfc_path = cfc_path[1:-1]
        if is_cfc_dot_path(cfc_path):
            file_path, dot_path = get_cfc_file_info(cfml_view, cfc_path)
            if file_path:
                return cfc_path, file_path, dot_path, None, [r]

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
                    "meta.instance.constructor.cfml",
                ):
                    r = utils.get_scope_region_containing_point(
                        cfml_view.view,
                        dot_context[-1].name_region.begin(),
                        "meta.instance.constructor.cfml",
                    )
                    cfc_path = cfml_view.view.substr(r)[4:].split("(")[0]
                    file_path, dot_path = get_cfc_file_info(cfml_view, cfc_path)
                    return (
                        cfc_path,
                        file_path,
                        dot_path,
                        function_name,
                        [r, funct_region],
                    )

                if cfml_view.view.match_selector(
                    dot_context[-1].name_region.begin(),
                    "meta.function-call.support.createcomponent.cfml",
                ):
                    r = utils.get_scope_region_containing_point(
                        cfml_view.view,
                        dot_context[-1].name_region.begin(),
                        "meta.function-call.support.createcomponent.cfml",
                    )
                    cfc_path = get_component_name(cfml_view.view.substr(r))
                    file_path, dot_path = get_cfc_file_info(cfml_view, cfc_path)
                    return (
                        cfc_path,
                        file_path,
                        dot_path,
                        function_name,
                        [r, funct_region],
                    )

                if is_possible_cfc_instance(dot_context):
                    cfc_path, file_path, dot_path, temp, regions = find_cfc_by_var_assignment(
                        cfml_view, position, dot_context[0].name
                    )
                    if regions:
                        regions.append(dot_context[0].name_region)
                        regions.append(funct_region)
                    return cfc_path, file_path, dot_path, function_name, regions

    if cfml_view.view.match_selector(position, "variable.other, meta.property.cfml"):
        var_region = cfml_view.view.word(position)
        dot_context = cfml_view.get_dot_context(var_region.begin() - 1)
        if len(dot_context) == 0 or (
            len(dot_context) == 1 and dot_context[0].name == "variables"
        ):
            cfc_path, file_path, dot_path, temp, regions = find_cfc_by_var_assignment(
                cfml_view, position, cfml_view.view.substr(var_region).lower()
            )
            if regions:
                regions.append(var_region)
            return cfc_path, file_path, dot_path, temp, regions

    return None, None, None, None, None


def find_cfc_by_var_assignment(cfml_view, position, var_name):
    empty_tuple = None, None, None, None, None

    if not utils.get_setting("instantiated_component_completions"):
        return empty_tuple

    var_assignment_region = cfml_view.find_variable_assignment(position, var_name)
    if not var_assignment_region:
        return empty_tuple

    s = component_selector + "," + constructor_selector
    if not cfml_view.view.match_selector(var_assignment_region.end(), s):
        return empty_tuple

    # try to determine component
    cfc_path, file_path, dot_path, function_name, regions = find_cfc(
        cfml_view, var_assignment_region.end()
    )

    if cfc_path is None:
        return empty_tuple

    regions.append(var_assignment_region)
    next_pt = utils.get_next_character(cfml_view.view, regions[0].end())

    if cfml_view.view.substr(next_pt) != ".":
        return cfc_path, file_path, dot_path, function_name, regions

    # if next char is a `.`, try to determine if what follows is init method
    if not cfml_view.view.match_selector(next_pt + 1, "meta.function-call.method"):
        return empty_tuple

    function_name, function_name_region, function_args_region = cfml_view.get_function_call(
        next_pt + 1
    )

    if not function_name:
        return empty_tuple

    metadata = component_index.get_extended_metadata_by_file_path(
        cfml_view.project_name, file_path
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

    return cfc_path, file_path, dot_path, function_name, regions


def get_cfc_file_info(cfml_view, cfc_path):
    if not cfc_path:
        return None, None

    cfc_dot_path = component_index.get_file_path_by_dot_path(
        cfml_view.project_name, cfc_path.lower()
    )
    if not cfc_dot_path:
        folder_cfc_path = get_folder_cfc_path(cfml_view, cfc_path)
        if folder_cfc_path:
            cfc_dot_path = component_index.get_file_path_by_dot_path(
                cfml_view.project_name, folder_cfc_path.lower()
            )

    if cfc_dot_path:
        return cfc_dot_path["file_path"], cfc_dot_path["dot_path"]

    # at this point, we know the cfc dot path is not one that is indexed in the model index
    # but we might be able to find it via mappings
    if cfml_view.project_name:
        mappings = cfml_view.view.window().project_data().get("mappings", [])
        mapped_cfc_path = "/" + cfc_path.lower().replace(".", "/") + ".cfc"
        for mapping in mappings:
            normalized_mapping = utils.normalize_mapping(
                mapping, cfml_view.project_name
            )
            if mapped_cfc_path.lower().startswith(normalized_mapping["mapping"]):
                relative_path = mapped_cfc_path.replace(
                    normalized_mapping["mapping"], ""
                )[1:]
                relative_path, path_exists = utils.get_verified_path(
                    normalized_mapping["path"], relative_path
                )
                if path_exists:
                    full_file_path = normalized_mapping["path"] + "/" + relative_path
                    return full_file_path, None

    # last option is to do a relative search from the directory of the current file
    if cfml_view.file_path:
        directory = "/".join(cfml_view.file_path.split("/")[:-1])
        relative_path, path_exists = utils.get_verified_path(
            directory, cfc_path.lower().replace(".", "/") + ".cfc"
        )
        if path_exists:
            full_file_path = directory + "/" + relative_path
            return full_file_path, None

    return None, None
