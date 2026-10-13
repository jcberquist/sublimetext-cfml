import os
import sublime
from ...component_index import component_index, dot_paths, to_completion_item
from ...component_index.completions import escape_snippet_text
from ... import kinds
from ... import utils
from . import cfc_utils


# by project name: for a project with cfc_folders, the completions of each
# lower case dot path through its mappings; for a project whose components
# are found in the folders of its window, its data and what
# get_automatic_completions() needs to find the completions asked for
projects = {}


def build_project_map(project_name, project_data):
    if project_data is None:
        projects.pop(project_name, None)
        return

    if project_data['automatic']:
        previous = projects.get(project_name)
        # most publications are a save of a file already in the index
        if (
            previous
            and 'children' in previous
            and previous['project_data']['index'].keys() == project_data['index'].keys()
        ):
            children = previous['children']
        else:
            children = build_children(project_data['index'])
        projects[project_name] = {
            'project_data': project_data,
            'path_map': map_paths(project_data['dot_paths']),
            'children': children,
        }
        return

    path_completions, constructor_completions = make_completions(project_data)
    projects[project_name] = {
        'path_completions': path_completions,
        'constructor_completions': constructor_completions,
    }


def build_children(file_paths):
    """
    Returns the names of the components and of the folders that hold
    components at some depth in each folder, by lower case folder path, as
    pairs of the name cased as in the file system and whether it is a
    component. Every folder above a component file is in it, as a dot path
    relative to the folder of a file can start above the folders of the
    window.
    """
    children = {}
    for file_path in file_paths:
        folder, name = file_path.rsplit('/', 1)
        # component files end in .cfc
        children.setdefault(folder.lower(), set()).add((name[:-4], True))
        while '/' in folder:
            parent, name = folder.rsplit('/', 1)
            names = children.setdefault(parent.lower(), set())
            if (name, False) in names:
                # and so are the folders above it
                break
            names.add((name, False))
            folder = parent
    return children


def make_completions(project_data):
    dot_paths = project_data['dot_paths']
    path_map = map_paths(dot_paths)
    path_completions = {}
    constructor_completions = {}
    for k in path_map:
        path_completions[k] = []
        constructor_completions[k] = []
        for c in sorted(path_map[k], key=lambda i: i['path_part']):
            path_completions[k].append(make_completion(c, k, project_data, False))
            constructor_completions[k].append(make_completion(c, k, project_data, True))
    return path_completions, constructor_completions


def make_completion(path_part_dict, key, project_data, constructor):
    file_path = None
    if path_part_dict['is_cfc'] and constructor:
        full_key = key + ('.' if len(key) > 0 else '') + path_part_dict['path_part']
        file_path = project_data['dot_paths'][full_key.lower()]['file_path']
    return make_item(
        path_part_dict['path_part'],
        path_part_dict['is_cfc'],
        constructor,
        file_path,
        project_data,
    )


def make_item(path_part, is_cfc, constructor, file_path, project_data):
    """
    Returns the completion of a folder or component name in a dot path. A
    component's completion in a constructor has the arguments of the
    constructor of the file at file_path, and empty parentheses when there
    is no file or it has no constructor.
    """
    # the completion is a snippet, so \ and $ in a folder or file name are
    # escaped
    completion = escape_snippet_text(path_part)
    if is_cfc and constructor:
        # None for a value of the setting that is not a completion type
        completions = (
            project_data['completions'][file_path].get(
                utils.get_setting('cfml_cfc_completions')
            )
            if file_path
            else None
        )
        if completions and completions['constructor']:
            # the arguments, after the name of the constructor
            content = completions['constructor'].content
            completion = completion + content[content.index('(') :]
        else:
            completion = completion + '()'
    if not is_cfc:
        completion += '.'
    return sublime.CompletionItem(
        path_part,
        'cfc' if is_cfc else 'cfc path',
        completion,
        sublime.CompletionFormat.SNIPPET,
        kind=kinds.COMPONENT if is_cfc else kinds.PACKAGE,
    )


def map_paths(dot_paths):
    path_map = {}
    for path_key in dot_paths:
        path_parts = dot_paths[path_key]['dot_path'].split('.')
        for i in range(len(path_parts)):
            key = '.'.join(path_parts[:i]).lower()
            if key not in path_map:
                path_map[key] = []
            is_cfc = i == len(path_parts) - 1
            path_part_dict = {'path_part': path_parts[i], 'is_cfc': is_cfc}
            if path_part_dict not in path_map[key]:
                path_map[key].append(path_part_dict)
    return path_map


def get_tag_attributes(cfml_view):
    if not cfml_view.project_name or cfml_view.project_name not in projects:
        return None

    if cfml_view.view.match_selector(
        cfml_view.position - 1,
        'meta.class.inheritance.cfml -entity.other.inherited-class.cfml',
    ):
        cfc_path = ''
        completions = get_path_completions(cfml_view, cfc_path, 'path_completions')
        if len(completions) > 0:
            return completions

    if cfml_view.view.match_selector(
        cfml_view.position - 1, 'entity.other.inherited-class.cfml'
    ):
        r = utils.get_scope_region_containing_point(
            cfml_view.view, cfml_view.position - 1, 'entity.other.inherited-class.cfml'
        )
        if r is None:
            return None
        r = sublime.Region(r.begin(), cfml_view.position - len(cfml_view.prefix))
        cfc_path = '.'.join(cfml_view.view.substr(r).split('.')[:-1])
        completions = get_path_completions(cfml_view, cfc_path, 'path_completions')
        if len(completions) > 0:
            return completions


def get_script_completions(cfml_view):
    if not cfml_view.project_name or cfml_view.project_name not in projects:
        return None

    if cfml_view.view.match_selector(
        cfml_view.position,
        'meta.function-call.support.createcomponent.cfml string.quoted',
    ):
        r = utils.get_scope_region_containing_point(
            cfml_view.view, cfml_view.position, 'string.quoted'
        )
        if r is None:
            return None
        r = sublime.Region(r.begin(), cfml_view.position + 1)
        cfc_path = cfml_view.view.substr(r)
        if cfc_path[0] not in ['"', "'"] or cfc_path[-1] not in ['"', "'"]:
            return None
        cfc_path = '.'.join(cfc_path[1:-1].split('.')[:-1])
        completions = get_path_completions(cfml_view, cfc_path, 'path_completions')
        if len(completions) > 0:
            return completions

    if cfml_view.view.match_selector(
        cfml_view.position - 1, 'meta.instance.constructor.cfml'
    ):
        r = utils.get_scope_region_containing_point(
            cfml_view.view, cfml_view.position - 1, 'meta.instance.constructor.cfml'
        )
        if r is None:
            return None
        r = sublime.Region(r.begin(), cfml_view.position - len(cfml_view.prefix))
        cfc_path = cfc_utils.get_constructor_path(cfml_view.view.substr(r))
        if cfc_path is None:
            return None
        completions = get_path_completions(
            cfml_view, '.'.join(cfc_path.split('.')[:-1]), 'constructor_completions'
        )
        if len(completions) > 0:
            return completions

    return None


def get_dot_completions(cfml_view):
    if not cfml_view.project_name or len(cfml_view.dot_context) == 0:
        return None

    component_selector = 'meta.function-call.support.createcomponent.cfml'
    constructor_selector = 'meta.instance.constructor.cfml'
    component_name = None
    constructor_region = utils.get_scope_region_containing_point(
        cfml_view.view, cfml_view.prefix_start - 2, constructor_selector
    )

    if cfml_view.dot_context[
        0
    ].name == 'createobject' and cfml_view.view.match_selector(
        cfml_view.prefix_start - 2, component_selector
    ):
        component_name = cfc_utils.get_component_name(
            cfml_view.view.substr(cfml_view.dot_context[0].args_region)
        )
    elif constructor_region:
        # only a dot right after the constructor, not in its dot path or
        # its arguments
        if constructor_region.end() == cfml_view.prefix_start - 1:
            component_name = cfc_utils.get_constructor_path(
                cfml_view.view.substr(constructor_region)
            )
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
            return completions

    return None


def get_path_completions(cfml_view, cfc_path, completion_type):
    """
    Returns the completions of the next part of a dot path, after cfc_path,
    which is what is typed before the last dot; empty when nothing is.
    """
    project = projects[cfml_view.project_name]
    if 'children' in project:
        return get_automatic_completions(
            project, cfml_view, cfc_path, completion_type == 'constructor_completions'
        )
    folder_cfc_path = cfc_utils.get_folder_cfc_path(cfml_view, cfc_path)
    return [
        *get_completions(cfml_view.project_name, cfc_path, completion_type),
        *get_completions(cfml_view.project_name, folder_cfc_path, completion_type),
    ]


def get_automatic_completions(project, cfml_view, cfc_path, constructor):
    """
    Returns the completions of the next part of a dot path in a project
    whose components are found in the folders of its window: the children
    of the folders that the dot path typed so far can name by the rules of
    dot_paths.py. That is the folder of the view's file, the mappings and
    each folder of the window, and after `a.b.` also every folder whose
    folder chain ends in a.b. A name is offered once, cased as in the first
    of these that has it, and a component in a constructor has the
    arguments of the file that the dot path resolves to.
    """
    project_data = project['project_data']
    children = project['children']
    key = cfc_path.lower()

    # the folders that the dot path typed so far names: down from the folder
    # of the view's file (rule 1), through the mappings (rule 2), down from
    # each folder of the window (rule 3), and any folder whose chain ends in
    # it (rule 4)
    relative_path = '/' + key.replace('.', '/') if key else ''
    folders = [folder.lower() + relative_path for folder in project_data['discoveries']]
    folders.extend(
        folder.lower() for folder in project_data['folder_suffixes'].get(key, [])
    )

    names = {}

    def offer(found):
        for name, is_cfc in sorted(found):
            names.setdefault((name.lower(), is_cfc), name)

    if cfml_view.file_path:
        folder = os.path.dirname(cfml_view.file_path).lower() + relative_path
        offer(children.get(folder, ()))
    offer(
        (part['path_part'], part['is_cfc']) for part in project['path_map'].get(key, [])
    )
    for folder in folders:
        offer(children.get(folder, ()))

    completions = []
    for (_, is_cfc), name in sorted(names.items(), key=lambda item: item[1]):
        file_path = None
        if is_cfc and constructor:
            dot_path = cfc_path + '.' + name if cfc_path else name
            resolution = dot_paths.resolve(project_data, dot_path, cfml_view.file_path)
            file_path = resolution.file_paths[0] if resolution.file_paths else None
        completions.append(
            make_item(name, is_cfc, constructor, file_path, project_data)
        )
    return completions


def get_completions(project_name, cfc_path, completion_type):
    if (
        cfc_path is not None
        and cfc_path.lower() in projects[project_name][completion_type]
    ):
        return projects[project_name][completion_type][cfc_path.lower()]
    return []


def get_completions_by_component_name(cfml_view, component_name):
    comp = component_index.get_completions_by_dot_path(
        cfml_view.project_name, component_name, cfml_view.file_path
    )

    if comp:
        filtered_completions = []
        for completion in comp['functions']:
            if not completion.private:
                filtered_completions.append(to_completion_item(completion))
        return filtered_completions

    return None
