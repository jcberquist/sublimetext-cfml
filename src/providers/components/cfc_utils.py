import re
import sublime
from typing import NamedTuple
from ...component_index import component_index
from ...component_reference import ComponentReference
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
    return component_index.get_folder_mapping(
        cfml_view.project_name, cfml_view.file_path
    )


def find_reference(cfml_view, position):
    """
    Returns a ComponentReference to the component, or the method of one,
    that a position is on, or None. The component is named by its dot path,
    or as it is written when its file is not in a mapped folder.
    """
    cfc_path, file_path, dot_path, function_name, regions = find_cfc(
        cfml_view, position
    )
    if not cfc_path or not file_path or not regions:
        return None
    name = dot_path or cfc_path
    # the other files the dot path resolves to
    resolution = resolve_cfc(cfml_view, cfc_path)
    if resolution is None or resolution.file_paths[0] != file_path:
        resolution = CfcResolution([file_path], dot_path)
    return ComponentReference(
        file_path,
        name,
        function_name,
        [r for r in regions if r is not None],
        name.split(".").pop(),
        tuple(resolution.file_paths[1:]),
        resolution.guessed,
    )


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

    if cfml_view.view.match_selector(position, "variable.other"):
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

    if not component_index.is_init_method(
        cfml_view.project_name, file_path, function_name
    ):
        return empty_tuple

    next_pt = utils.get_next_character(cfml_view.view, function_args_region.end())

    if cfml_view.view.substr(next_pt) == ".":
        return empty_tuple

    return cfc_path, file_path, dot_path, function_name, regions


class CfcResolution(NamedTuple):
    """The component files that a dot path written in a view resolves to."""

    # best first, never empty
    file_paths: list[str]
    # the dot path the docs show, None for a file that is not indexed
    dot_path: str | None
    # whether the files only share a name with the dot path
    guessed: bool = False


def resolve_cfc(cfml_view, cfc_path):
    """
    Returns the files that a dot path written in the view resolves to, or
    None. The rules of the component index that are certain, relative to
    the file and through the mappings, come first; then the same two on
    disk, for a file that is not indexed or a view with no project; then
    the other rules of the index.
    """
    if not cfc_path:
        return None

    project_name = cfml_view.project_name
    resolution = component_index.resolve_dot_path(
        project_name, cfc_path, cfml_view.file_path
    )

    def resolved():
        file_path = resolution.file_paths[0]
        dot_path = component_index.get_dot_path_name(
            project_name, file_path, cfc_path, resolution
        )
        return CfcResolution(resolution.file_paths, dot_path, resolution.guessed)

    if resolution.rule in (1, 2):
        return resolved()

    file_path = find_cfc_on_disk(cfml_view, cfc_path)
    if file_path:
        return CfcResolution([file_path], None)

    if resolution.file_paths:
        return resolved()
    return None


def find_cfc_on_disk(cfml_view, cfc_path):
    """
    Returns the file of a dot path found on disk through the mappings of the
    project, or else relative to the folder of the view's file, or None.
    """
    if cfml_view.project_name:
        mappings = component_index.get_project_data(cfml_view.project_name).get(
            "mappings", []
        )
        base_dir = component_index.get_base_dir(cfml_view.project_name)
        mapped_cfc_path = "/" + cfc_path.lower().replace(".", "/") + ".cfc"
        for mapping in mappings:
            normalized_mapping = utils.normalize_mapping(mapping, base_dir)
            # dot paths are case insensitive, so the mapping is too
            mapping_prefix = normalized_mapping["mapping"].lower()
            if not mapped_cfc_path.startswith(mapping_prefix + "/"):
                continue
            relative_path, path_exists = utils.get_verified_path(
                normalized_mapping["path"], mapped_cfc_path[len(mapping_prefix) + 1 :]
            )
            if path_exists:
                return normalized_mapping["path"] + "/" + relative_path

    if cfml_view.file_path:
        directory = "/".join(cfml_view.file_path.split("/")[:-1])
        relative_path, path_exists = utils.get_verified_path(
            directory, cfc_path.lower().replace(".", "/") + ".cfc"
        )
        if path_exists:
            return directory + "/" + relative_path

    return None


def get_cfc_file_info(cfml_view, cfc_path):
    """
    Returns the best file that a dot path written in the view resolves to
    and the dot path the docs show for it, or None for both.
    """
    resolution = resolve_cfc(cfml_view, cfc_path)
    if resolution is None:
        return None, None
    return resolution.file_paths[0], resolution.dot_path
