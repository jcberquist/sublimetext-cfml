import sublime
from ...component_index import component_index
from ... import utils
from . import cfc_utils


projects = {}


def build_project_map(project_name):
    global projects
    data = {}
    path_completions, constructor_completions = make_completions(project_name)
    data["path_completions"] = path_completions
    data["constructor_completions"] = constructor_completions
    projects[project_name] = data


def make_completions(project_name):
    dot_paths = component_index.get_dot_paths(project_name)
    path_map = map_paths(dot_paths)
    path_completions = {}
    constructor_completions = {}
    for k in path_map:
        path_completions[k] = []
        constructor_completions[k] = []
        for c in sorted(path_map[k], key=lambda i: i["path_part"]):
            path_completions[k].append(
                make_completion(c, k, dot_paths, project_name, False)
            )
            constructor_completions[k].append(
                make_completion(c, k, dot_paths, project_name, True)
            )
    return path_completions, constructor_completions


def make_completion(path_part_dict, key, dot_paths, project_name, constructor):
    completion = path_part_dict["path_part"]
    if path_part_dict["is_cfc"] and constructor:
        full_key = key + ("." if len(key) > 0 else "") + completion
        constructor_completion = component_index.get_completions_by_file_path(
            project_name, dot_paths[full_key.lower()]["file_path"]
        )["constructor"]
        if constructor_completion:
            completion = completion + constructor_completion.content[4:]
        else:
            completion = completion + "()"
    if not path_part_dict["is_cfc"]:
        completion += "."
    return (
        path_part_dict["path_part"]
        + "\t"
        + ("cfc" if path_part_dict["is_cfc"] else "cfc path"),
        completion,
    )


def map_paths(dot_paths):
    path_map = {}
    for path_key in dot_paths:
        path_parts = dot_paths[path_key]["dot_path"].split(".")
        for i in range(len(path_parts)):
            key = ".".join(path_parts[:i]).lower()
            if key not in path_map:
                path_map[key] = []
            is_cfc = i == len(path_parts) - 1
            path_part_dict = {"path_part": path_parts[i], "is_cfc": is_cfc}
            if path_part_dict not in path_map[key]:
                path_map[key].append(path_part_dict)
    return path_map


def get_tag_attributes(cfml_view):
    if not cfml_view.project_name or cfml_view.project_name not in projects:
        return None

    if cfml_view.view.match_selector(
        cfml_view.position - 1,
        "meta.class.inheritance.cfml -entity.other.inherited-class.cfml",
    ):
        cfc_path = ""
        folder_cfc_path = cfc_utils.get_folder_cfc_path(cfml_view, cfc_path)

        completions = []
        completions.extend(
            get_completions(cfml_view.project_name, cfc_path, "path_completions")
        )
        completions.extend(
            get_completions(cfml_view.project_name, folder_cfc_path, "path_completions")
        )

        if len(completions) > 0:
            return cfml_view.CompletionList(completions, 0, False)

    if cfml_view.view.match_selector(
        cfml_view.position - 1, "entity.other.inherited-class.cfml"
    ):
        r = utils.get_scope_region_containing_point(
            cfml_view.view, cfml_view.position - 1, "entity.other.inherited-class.cfml"
        )
        r = sublime.Region(r.begin(), cfml_view.position - len(cfml_view.prefix))
        cfc_path = ".".join(cfml_view.view.substr(r).split(".")[:-1])
        folder_cfc_path = cfc_utils.get_folder_cfc_path(cfml_view, cfc_path)

        completions = []
        completions.extend(
            get_completions(cfml_view.project_name, cfc_path, "path_completions")
        )
        completions.extend(
            get_completions(cfml_view.project_name, folder_cfc_path, "path_completions")
        )

        if len(completions) > 0:
            return cfml_view.CompletionList(completions, 0, False)


def get_script_completions(cfml_view):
    if not cfml_view.project_name or cfml_view.project_name not in projects:
        return None

    if cfml_view.view.match_selector(
        cfml_view.position,
        "meta.function-call.support.createcomponent.cfml string.quoted",
    ):
        r = utils.get_scope_region_containing_point(
            cfml_view.view, cfml_view.position, "string.quoted"
        )
        r = sublime.Region(r.begin(), cfml_view.position + 1)
        cfc_path = cfml_view.view.substr(r)
        if cfc_path[0] not in ['"', "'"] or cfc_path[-1] not in ['"', "'"]:
            return None
        cfc_path = ".".join(cfc_path[1:-1].split(".")[:-1])
        folder_cfc_path = cfc_utils.get_folder_cfc_path(cfml_view, cfc_path)

        completions = []
        completions.extend(
            get_completions(cfml_view.project_name, cfc_path, "path_completions")
        )
        completions.extend(
            get_completions(cfml_view.project_name, folder_cfc_path, "path_completions")
        )

        if len(completions) > 0:
            return cfml_view.CompletionList(completions, 0, False)

    if cfml_view.view.match_selector(
        cfml_view.position - 1, "meta.instance.constructor.cfml"
    ):
        r = utils.get_scope_region_containing_point(
            cfml_view.view, cfml_view.position - 1, "meta.instance.constructor.cfml"
        )
        r = sublime.Region(r.begin(), cfml_view.position - len(cfml_view.prefix))
        cfc_path = ".".join(cfml_view.view.substr(r)[4:].split(".")[:-1])
        folder_cfc_path = cfc_utils.get_folder_cfc_path(cfml_view, cfc_path)

        completions = []
        completions.extend(
            get_completions(cfml_view.project_name, cfc_path, "constructor_completions")
        )
        completions.extend(
            get_completions(
                cfml_view.project_name, folder_cfc_path, "constructor_completions"
            )
        )

        if len(completions) > 0:
            return cfml_view.CompletionList(completions, 0, False)

    return None


def get_dot_completions(cfml_view):
    if not cfml_view.project_name or len(cfml_view.dot_context) == 0:
        return None

    component_selector = "meta.function-call.support.createcomponent.cfml"
    constructor_selector = "meta.instance.constructor.cfml"
    component_name = None

    if cfml_view.dot_context[
        0
    ].name == "createobject" and cfml_view.view.match_selector(
        cfml_view.prefix_start - 2, component_selector
    ):
        component_name = cfc_utils.get_component_name(
            cfml_view.view.substr(cfml_view.dot_context[0].args_region)
        )
    elif cfml_view.view.match_selector(
        cfml_view.prefix_start - 2, constructor_selector
    ):
        component_name = ".".join([s.name for s in reversed(cfml_view.dot_context)])
    elif cfc_utils.is_possible_cfc_instance(cfml_view.dot_context):
        # look for variable assignment, it might be an instantiated component
        component_tuple = cfc_utils.find_cfc_by_var_assignment(
            cfml_view, cfml_view.prefix_start, cfml_view.dot_context[0].name
        )
        if component_tuple[0] is not None:
            component_name = component_tuple[0]

    if component_name:
        completions = get_completions_by_component_name(cfml_view, component_name)
        if completions:
            return cfml_view.CompletionList(completions, 0, False)

    return None


def get_completions(project_name, cfc_path, completion_type):
    if (
        cfc_path is not None
        and cfc_path.lower() in projects[project_name][completion_type]
    ):
        return projects[project_name][completion_type][cfc_path.lower()]
    return []


def get_completions_by_component_name(cfml_view, component_name):
    comp = component_index.get_completions_by_dot_path(
        cfml_view.project_name, component_name.lower()
    )

    if not comp:
        folder_cfc_path = cfc_utils.get_folder_cfc_path(cfml_view, component_name)
        if folder_cfc_path:
            comp = component_index.get_completions_by_dot_path(
                cfml_view.project_name, folder_cfc_path
            )

    if comp:
        filtered_completions = []
        for completion in comp["functions"]:
            if not completion.private:
                filtered_completions.append(
                    (completion.key + "\t" + completion.hint, completion.content)
                )
        return filtered_completions

    return None
