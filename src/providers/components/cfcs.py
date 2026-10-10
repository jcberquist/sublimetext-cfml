import sublime
import os
import re
from typing import NamedTuple
from ...component_index import candidates, component_index, to_completion_item
from ... import utils


class CfcInfo(NamedTuple):
    """A component that a variable name is given to."""

    # the variable name, cased as the template that gives it
    name: str
    file_path: str
    # whether completions offer the accessors of the component's properties
    accessors: bool
    # whether the name is a guess, rather than one the project file gives
    guessed: bool


# by project, the components that each lower case variable name is given
# to, in the order they are indexed; a name given to two components is
# given to both
projects: dict[str, dict[str, list[CfcInfo]]] = {}

# the cfml_auto_variable_names setting when it is not a list
DEFAULT_AUTO_VARIABLE_NAMES = ['{cfc}', '{cfc}{cfc_folder_singularized}']

# what a variable name template can hold
PLACEHOLDER = re.compile(
    r'(\{(?:cfc|entity_name|cfc_folder|cfc_folder_singularized)\})'
)

# the scopes of CFML: `application.` is not a call on Application.cfc
SCOPE_NAMES = frozenset(
    [
        'application',
        'arguments',
        'cgi',
        'client',
        'cookie',
        'form',
        'local',
        'request',
        'server',
        'session',
        'super',
        'this',
        'thread',
        'url',
        'variables',
    ]
)


def build_project_cfcs(project_name, project_data):
    if project_data is None:
        projects.pop(project_name, None)
        return

    if project_data['automatic']:
        templates = get_auto_variable_names(project_name)
        projects[project_name] = build_auto_cfcs(templates, project_data['index'])
        return

    cfc_index: dict[str, list[CfcInfo]] = {}
    cfc_folders = component_index.get_project_data(project_name).get('cfc_folders', [])
    base_dir = component_index.get_base_dir(project_name)
    for cfc_folder in cfc_folders:
        variable_names = cfc_folder.get('variable_names', [])
        if variable_names:
            accessors = cfc_folder.get('accessors', True)
            if not isinstance(accessors, bool):
                accessors = True
            build_cfcs(
                cfc_index,
                cfc_folder['path'],
                variable_names,
                accessors,
                base_dir,
                project_data['index'],
            )
    projects[project_name] = cfc_index


def build_cfcs(cfc_index, root_path, cfc_names, accessors, base_dir, index):
    """Adds the names that a cfc folder gives its components to cfc_index."""
    root_dir = utils.normalize_path(root_path, base_dir)
    templates = compile_templates(cfc_names)
    for file_path, metadata in index.items():
        if not file_path.startswith(root_dir + '/'):
            continue
        for cfc_name in get_cfc_names(root_dir, templates, file_path, metadata):
            add_cfc(cfc_index, CfcInfo(cfc_name, file_path, accessors, False))


def get_auto_variable_names(project_name):
    """
    Returns the templates of the names that the components of a project in
    automatic mode are given, which its project file can set.
    """
    templates = utils.get_project_data_setting(
        component_index.get_project_data(project_name), 'cfml_auto_variable_names'
    )
    if not isinstance(templates, list):
        templates = DEFAULT_AUTO_VARIABLE_NAMES
    return [
        template for template in templates if isinstance(template, str) and template
    ]


def build_auto_cfcs(templates, index) -> dict[str, list[CfcInfo]]:
    """
    Returns the names that the templates give every component of an index,
    a guess at how the code refers to it; the folder of a template is the
    folder the file is in. The names of the scopes are left out.
    """
    cfc_index: dict[str, list[CfcInfo]] = {}
    templates = compile_templates(templates)
    if not templates:
        return cfc_index
    # this runs at each publication of the index, so it is kept lean
    for file_path, metadata in index.items():
        folder_end = file_path.rfind('/')
        folder_start = file_path.rfind('/', 0, folder_end)
        # every component file ends in .cfc
        cfc = file_path[folder_end + 1 : -4]
        folder = file_path[folder_start + 1 : folder_end]
        for cfc_name in make_names(templates, cfc, folder, metadata):
            key = cfc_name.lower()
            if key in SCOPE_NAMES:
                continue
            found = cfc_index.get(key)
            if found is None:
                cfc_index[key] = [CfcInfo(cfc_name, file_path, True, True)]
            # the file's names are added together, so a name that two
            # templates give it is last in the list
            elif found[-1].file_path != file_path:
                found.append(CfcInfo(cfc_name, file_path, True, True))
    return cfc_index


def add_cfc(cfc_index, cfc_info: CfcInfo):
    # a file is given a name once, by the first folder or template to give it
    found = cfc_index.setdefault(cfc_info.name.lower(), [])
    if all(other.file_path != cfc_info.file_path for other in found):
        found.append(cfc_info)


def get_cfc_names(root_dir, templates, file_path, metadata):
    # the folder is the one the file is in below the cfc folder, if any
    cfc_path, file_ext = os.path.splitext(file_path)
    cfc_path_parts = cfc_path.replace(root_dir, '').split('/')
    folder = cfc_path_parts[-2] if len(cfc_path_parts) > 1 else ''
    return make_names(templates, cfc_path_parts[-1], folder, metadata)


def compile_templates(templates):
    """
    Returns the variable name templates as format strings, in which only
    the placeholders are fields.
    """
    return [
        ''.join(
            part if i % 2 else part.replace('{', '{{').replace('}', '}}')
            for i, part in enumerate(PLACEHOLDER.split(template))
        )
        for template in templates
    ]


def make_names(templates, cfc, folder, metadata):
    cfc_folder = uppercase(folder)
    path_keys = {
        'cfc': cfc,
        'entity_name': metadata['entityname'] or cfc,
        'cfc_folder': cfc_folder,
        'cfc_folder_singularized': (
            cfc_folder[:-1] if cfc_folder.endswith('s') else cfc_folder
        ),
    }
    return [template.format_map(path_keys) for template in templates]


def get_cfc_list(project_name):
    """
    Returns the variable names of a project's components, each once, cased
    as the first component given it has it.
    """
    if project_name in projects:
        return [
            projects[project_name][key][0].name
            for key in sorted(projects[project_name])
        ]
    return []


def has_cfc(project_name, cfc_name):
    if project_name in projects:
        return cfc_name.lower() in projects[project_name]
    return False


def search_dot_context_for_cfc(project_name, dot_context):
    """
    Returns the name of the cfc that the variable names of a dot context
    refer to and the region of those names, or None.
    """
    stack = []
    regions = []
    for symbol in dot_context:
        if not symbol.is_function:
            stack.append(symbol.name)
            regions.append(symbol.name_region)
        else:
            if len(stack) > 0:
                break

    if len(stack) > 0:
        stack.reverse()
        regions.reverse()
        for i in range(len(stack)):
            cfc_name = '.'.join(stack[i:])
            if has_cfc(project_name, cfc_name):
                return cfc_name, sublime.Region(regions[i].begin(), regions[-1].end())
    return None


def find_cfc_in_dot_context(project_name, dot_context):
    """
    As search_dot_context_for_cfc(), but a cfc can also be referred to by
    a getter for it: getUserService().
    """
    found = search_dot_context_for_cfc(project_name, dot_context)
    if found:
        return found

    if len(dot_context) > 0:
        symbol = dot_context[-1]
        if (
            symbol.is_function
            and symbol.name.startswith('get')
            and has_cfc(project_name, symbol.name[3:])
        ):
            return symbol.name[3:], symbol.name_region

    return None


def lookup(
    project_name, cfc_names, from_file=None, function_name=None
) -> list[CfcInfo]:
    """
    Returns the components that variable names are given to, best first:
    those of the first name, then those of the next that are not already
    found, the components of each name ranked by candidates.rank() from the
    file the names are written in, with identical copies collapsed. When a
    method is called on the name, only the components that have it,
    inherited methods included, are kept, unless none has it.
    """
    cfc_index = projects.get(project_name, {})
    project_data = component_index.data.get(project_name)
    found: dict[str, CfcInfo] = {}
    for cfc_name in cfc_names:
        by_file_path = {}
        for cfc_info in cfc_index.get(cfc_name.lower(), []):
            by_file_path.setdefault(cfc_info.file_path, cfc_info)
        file_paths = list(by_file_path)
        if project_data and len(file_paths) > 1:
            file_paths = candidates.rank(
                file_paths,
                project_data['index'],
                project_data['install_paths'],
                from_file,
            )
        for file_path in file_paths:
            found.setdefault(file_path, by_file_path[file_path])

    return narrow(project_name, list(found.values()), function_name)


def lookup_class(project_name, dot_path, function_name=None) -> list[CfcInfo]:
    """
    Returns the components of a class by its full dot path, best first, as
    lookup() does for a variable name; a framework object is of such a
    class. A file that only shares the class's name is another component
    (the config/Router.cfc of an app extends the framework's Router), so a
    dot path that resolves only by the file name gives none.
    """
    resolution = component_index.resolve_dot_path(project_name, dot_path)
    if resolution.guessed:
        return []
    cfc_infos = [
        CfcInfo(file_path[file_path.rfind('/') + 1 : -4], file_path, True, False)
        for file_path in resolution.file_paths
    ]
    return narrow(project_name, cfc_infos, function_name)


def narrow(project_name, cfc_infos: list[CfcInfo], function_name=None) -> list[CfcInfo]:
    """
    Returns the components that have a method, inherited methods included,
    or all of them when none has it or no method is called.
    """
    if function_name and len(cfc_infos) > 1:
        having = [
            cfc_info
            for cfc_info in cfc_infos
            if has_method(project_name, cfc_info.file_path, function_name)
        ]
        if having:
            return having
    return cfc_infos


def has_method(project_name, file_path, function_name):
    metadata = component_index.get_extended_metadata_by_file_path(
        project_name, file_path
    )
    return metadata is not None and function_name.lower() in metadata['functions']


def get_completions(project_name, found: list[CfcInfo]):
    """
    Returns the completions of the public methods of the components that a
    name could be, best first. When there are several, each method is
    offered once per component that has it, and its annotation tells the
    components apart.
    """
    if len(found) > 1:
        annotations = tell_apart([cfc_info.file_path for cfc_info in found])
    else:
        annotations = [None] * len(found)

    filtered_completions = []
    for cfc_info, annotation in zip(found, annotations, strict=True):
        cfc_completions = component_index.get_completions_by_file_path(
            project_name, cfc_info.file_path
        )
        # None when the file has left the index, or the cfml_cfc_completions
        # setting is not a completion type
        if cfc_completions is None:
            continue
        for completion in cfc_completions['functions']:
            if not completion.private and (
                cfc_info.accessors or not completion.accessor
            ):
                filtered_completions.append(to_completion_item(completion, annotation))
    return filtered_completions


def tell_apart(file_paths):
    """
    Returns the end of each component file's path that tells it from the
    others: its folder and name, and as few more folders as it takes.
    """
    parts = [file_path[:-4].split('/') for file_path in file_paths]
    for count in range(2, max(len(p) for p in parts)):
        ends = ['/'.join(p[-count:]) for p in parts]
        if len({end.lower() for end in ends}) == len(ends):
            return ends
    return [file_path[:-4] for file_path in file_paths]


def uppercase(string):
    if len(string) == 0:
        return ''
    return string[0].upper() + string[1:]
