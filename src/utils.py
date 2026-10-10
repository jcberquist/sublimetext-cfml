import functools
import json
import sublime
import os
import traceback
from collections import namedtuple
from typing import Any, cast, overload

Symbol = namedtuple(
    'Symbol', 'name is_function function_region args_region name_region'
)


def get_plugin_name():
    # the first part of this module's name is the package in Packages/
    return __name__.split('.')[0]


def package_resource_path(relative_path):
    return 'Packages/' + get_plugin_name() + '/' + relative_path


# the package's top-level syntaxes: CFML for components and templates
# (scope embedding.cfml), CFScript (CFML) for .cfs script files (scope
# source.cfml.script, the scope of the script inside CFML files)
CFML_SYNTAXES = (
    'syntaxes/CFML.sublime-syntax',
    'syntaxes/CFScript (CFML).sublime-syntax',
)


def is_cfml_view(settings):
    """
    Returns whether the settings are those of a view with one of the
    package's top-level syntaxes: what a ViewEventListener is given to
    decide whether it applies to a view.
    """
    syntax = settings.get('syntax')
    return any(syntax == package_resource_path(path) for path in CFML_SYNTAXES)


def expand_variables(template: str, variables) -> str:
    # sublime.expand_variables() accepts any JSON value; templates are strings
    return cast(str, sublime.expand_variables(template, variables))


def load_json_resource(relative_path):
    return json.loads(sublime.load_resource(package_resource_path(relative_path)))


@functools.cache
def load_template(relative_path):
    template = sublime.load_resource(
        package_resource_path('templates/' + relative_path)
    )
    return template.replace('\r', '')


def call_plugin_loaded(module):
    call_reporting_failure(module.__name__ + '._plugin_loaded()', module._plugin_loaded)


def call_reporting_failure(label, callback):
    # report a failure without stopping the caller from going on
    try:
        callback()
    except Exception:
        print('CFML: ' + label + ' failed')
        traceback.print_exc()


def get_window_folders(window) -> tuple[str, ...]:
    """Returns the folders of a window, normalized and sorted."""
    return tuple(sorted(normalize_path(folder) for folder in window.folders()))


def get_project_name(view):
    window = view.window()
    return get_project_name_from_window(window) if window else None


def get_project_name_from_window(window):
    """
    Returns the name of the window's project, which the indexes keep its
    data under: the path of the project file, or for a window with folders
    and no project file, a name made of the folders, so that windows on the
    same folders share a project. None for a window with neither. The name
    is a key, not a path to resolve anything against.
    """
    project_file_name = window.project_file_name()
    if project_file_name:
        return normalize_path(project_file_name)
    folders = get_window_folders(window)
    if folders:
        return 'folders:' + '|'.join(folders)
    return None


@overload
def normalize_path(path: str, root_path: str | None = None) -> str: ...
@overload
def normalize_path(path: None, root_path: str | None = None) -> None: ...
@overload
def normalize_path(path: str | None, root_path: str | None = None) -> str | None: ...


def normalize_path(path, root_path=None):
    if path is None:
        return None
    if not os.path.isabs(path) and root_path is not None:
        path = os.path.normpath(os.path.join(root_path, path))
    normalized_path = path.replace('\\', '/')
    if len(normalized_path) > 0 and normalized_path[-1] == '/':
        normalized_path = normalized_path[:-1]
    return normalized_path


def normalize_mapping(mapping, root_path=None):
    normalized_mapping = {}
    normalized_mapping['path'] = normalize_path(mapping['path'], root_path)
    normalized_mapping_path = mapping['mapping'].replace('\\', '/')
    if normalized_mapping_path[0] != '/':
        normalized_mapping_path = '/' + normalized_mapping_path
    if normalized_mapping_path[-1] == '/':
        normalized_mapping_path = normalized_mapping_path[:-1]
    normalized_mapping['mapping'] = normalized_mapping_path
    return normalized_mapping


def get_mapped_path_parts(file_path, mapping):
    """
    Returns the segments of file_path as seen through a normalized mapping,
    so with /site/model mapped to /model, /site/model/user.cfc gives
    ["model", "user.cfc"]. Returns None for a file outside the mapped folder.
    """
    if not file_path.startswith(mapping['path'] + '/'):
        return None
    mapped_path = mapping['mapping'] + file_path[len(mapping['path']) :]
    return mapped_path.split('/')[1:]


def find_symbol_location(window, symbol, file_path):
    locations = window.symbol_locations(
        symbol, sublime.SymbolSource.INDEX, sublime.SymbolType.DEFINITION
    )
    for location in locations:
        if normalize_path(location.path) == file_path:
            return location
    return None


WORD_OR_PUNCTUATION_END = (
    sublime.PointClassification.WORD_END | sublime.PointClassification.PUNCTUATION_END
)
WORD_OR_PUNCTUATION_START = (
    sublime.PointClassification.WORD_START
    | sublime.PointClassification.PUNCTUATION_START
)


def get_previous_character(view, position):
    if view.substr(position - 1) in [' ', '\t', '\n']:
        position = view.find_by_class(position, False, WORD_OR_PUNCTUATION_END)
    return position - 1


def get_next_character(view, position):
    if view.substr(position) in [' ', '\t', '\n']:
        position = view.find_by_class(position, True, WORD_OR_PUNCTUATION_START)
    return position


def get_previous_word(view, position):
    previous_character = get_previous_character(view, position)
    return view.substr(view.word(previous_character)).lower()


def merge_regions(regions):
    merged_regions = []
    for region in sorted(regions):
        if len(merged_regions) > 0 and merged_regions[-1].contains(region):
            continue
        elif len(merged_regions) > 0 and merged_regions[-1].end() == region.begin():
            merged_regions[-1] = sublime.Region(
                merged_regions[-1].begin(), region.end()
            )
        else:
            merged_regions.append(region)
    return merged_regions


def get_scope_region_containing_point(view, pt, scope):
    scope_count = view.scope_name(pt).count(scope) - view.scope_name(pt).count(
        '.' + scope
    )
    if scope_count == 0:
        return None
    # expand_to_scope() returns the outermost match, so repeat the scope to
    # the depth at pt to get the innermost region instead
    return view.expand_to_scope(pt, ' '.join([scope] * scope_count))


def get_char_point_before_scope(view, pt, scope):
    scope_region = get_scope_region_containing_point(view, pt, scope)
    if scope_region:
        scope_start = scope_region.begin()
        return get_previous_character(view, scope_start)
    return None


def get_dot_context(view, dot_position):
    context = []

    if view.substr(dot_position) != '.':
        return context

    if view.substr(dot_position - 1) in [' ', '\t', '\n']:
        dot_position = view.find_by_class(dot_position, False, WORD_OR_PUNCTUATION_END)

    base_scope_count = view.scope_name(dot_position).count('meta.function-call')
    scope_to_find = ' '.join(['meta.function-call'] * (base_scope_count + 1))
    function_call = None
    if view.match_selector(dot_position - 1, scope_to_find):
        function_call = get_function_call(view, dot_position - 1)
    if function_call:
        function_name, name_region, function_args_region = function_call
        context.append(
            Symbol(function_name, True, name_region, function_args_region, name_region)
        )
    elif view.match_selector(dot_position - 1, 'variable, meta.instance.constructor'):
        name_region = view.word(dot_position)
        context.append(
            Symbol(view.substr(name_region).lower(), False, None, None, name_region)
        )

    if len(context) > 0:
        context.extend(get_dot_context(view, name_region.begin() - 1))

    return context


def get_struct_context(view, position):
    context = []

    if not view.match_selector(position, 'meta.mapping.cfml'):
        return context

    previous_char_point = get_char_point_before_scope(
        view, position, 'meta.mapping.cfml'
    )
    if not view.match_selector(
        previous_char_point,
        'keyword.operator.assignment.cfml,punctuation.separator.key-value.cfml',
    ):
        return context

    previous_char_point = get_previous_character(view, previous_char_point)

    if not view.match_selector(previous_char_point, 'variable,meta.mapping.key.cfml'):
        return context

    name_region = view.word(previous_char_point)
    context.append(
        Symbol(view.substr(name_region).lower(), False, None, None, name_region)
    )

    if view.match_selector(previous_char_point, 'variable.other.member'):
        context.extend(get_dot_context(view, name_region.begin() - 1))
    else:
        context.extend(get_struct_context(view, name_region.begin()))

    return context


def get_setting(setting_key) -> Any:
    cfml_settings = sublime.load_settings('cfml_package.sublime-settings')
    return cfml_settings.get(setting_key)


def get_project_setting(window, setting_key) -> Any:
    """
    Returns a setting from the window's .sublime-project file if it is set
    there, and otherwise from the package settings.
    """
    project_data = {}
    if window and window.project_file_name():
        project_data = window.project_data() or {}
    return get_project_data_setting(project_data, setting_key)


def get_project_data_setting(project_data, setting_key) -> Any:
    """
    Returns a setting from the data of a project file if it is set there,
    and otherwise from the package settings: get_project_setting() for
    code that has a project's data, such as Project.data, but no window.
    """
    if setting_key in project_data:
        return project_data[setting_key]
    return get_setting(setting_key)


def get_tag_end(view, pos, is_cfml):
    tag_end = view.find('/?>', pos)
    if tag_end:
        if view.match_selector(tag_end.begin(), 'punctuation.definition.tag'):
            tag_end_is_cfml = view.match_selector(
                tag_end.begin(), 'punctuation.definition.tag.end.cfml'
            )
            if is_cfml == tag_end_is_cfml:
                return tag_end
        return get_tag_end(view, tag_end.end(), is_cfml)
    return None


def get_last_open_tag(view, pos, cfml_only, custom_tag_index):
    tag_selector = (
        'entity.name.tag.cfml, entity.name.tag.custom.cfml'
        if cfml_only
        else 'entity.name.tag'
    )
    closed_tags = []
    cfml_non_closing_tags = get_setting('cfml_non_closing_tags')
    html_non_closing_tags = get_setting('html_non_closing_tags')

    tag_name_regions = reversed(
        [r for r in view.find_by_selector(tag_selector) if r.end() <= pos]
    )

    for tag_name_region in tag_name_regions:
        # check for closing tag
        if view.substr(tag_name_region.begin() - 1) == '/':
            closed_tags.append(view.substr(tag_name_region))
            continue

        # this is an opening tag
        is_cfml = view.match_selector(
            tag_name_region.begin(), 'entity.name.tag.cfml, entity.name.tag.custom.cfml'
        )
        tag_end = get_tag_end(view, tag_name_region.end(), is_cfml)

        # if no tag end then give up
        if not tag_end:
            return None

        # if tag_end is after cursor position, then ignore it
        if tag_end.begin() > pos:
            continue

        # if tag_end length is 2 then this is a self closing tag so ignore it
        if tag_end.size() == 2:
            continue

        tag_name = view.substr(tag_name_region)

        if tag_name in closed_tags:
            closed_tags.remove(tag_name)
            continue

        # check to exclude cfml tags that should not have a closing tag
        if tag_name in cfml_non_closing_tags:
            continue
        # check to exclude html tags that should not have a closing tag
        if tag_name in html_non_closing_tags:
            continue
        # check for custom tags that should not be closed
        if view.match_selector(
            tag_name_region.begin(), 'meta.tag.custom.cfml'
        ) and tag_name not in custom_tag_index.get_closing_custom_tags(
            get_project_name(view)
        ):
            continue

        return tag_name

    return None


def get_tag_name(view, pos):
    tag_scope = 'meta.tag.cfml - punctuation.definition.tag.begin, meta.tag.custom.cfml - punctuation.definition.tag.begin, meta.tag.script.cfml, meta.tag.script.cf.cfml'
    tag_name_scope = (
        'entity.name.tag.cfml, entity.name.tag.custom.cfml, entity.name.tag.script.cfml'
    )
    # pos may also sit just after the end of a tag, or at the end of the
    # buffer with the tag still open, where there is no scope to expand
    # from: then the tag is the one at the position before
    tag_region = None
    if view.match_selector(pos, tag_scope):
        tag_region = view.expand_to_scope(pos, tag_scope)
    if tag_region is None and pos > 0 and view.match_selector(pos - 1, tag_scope):
        tag_region = view.expand_to_scope(pos - 1, tag_scope)
    if tag_region is None:
        return None

    # the name can be split over tokens, e.g. a custom tag's prefix
    name_region = None
    for r, scope in view.extract_tokens_with_scopes(tag_region):
        if sublime.score_selector(scope, tag_name_scope):
            if name_region is None:
                name_region = r
            elif r.begin() == name_region.end():
                name_region = name_region.cover(r)
            else:
                break
        elif name_region is not None:
            break

    return view.substr(name_region).lower() if name_region else None


def get_tag_attribute_name(view, pos):
    if view.match_selector(
        pos,
        'meta.tag entity.other.attribute-name.cfml, meta.class.declaration.cfml entity.other.attribute-name.cfml',
    ):
        return view.substr(view.word(pos)).lower()

    for scope in ['string.quoted', 'string.unquoted']:
        full_scope = (
            'meta.tag.cfml '
            + scope
            + ', meta.tag.custom.cfml '
            + scope
            + ', meta.tag.script.cfml '
            + scope
            + ', meta.tag.script.cf.cfml '
            + scope
            + ', meta.class.declaration.cfml '
            + scope
        )
        if view.match_selector(pos, full_scope):
            pos = get_char_point_before_scope(view, pos, scope)
            break

    full_scope = [
        'meta.tag.cfml punctuation.separator.key-value',
        'meta.tag.custom.cfml punctuation.separator.key-value',
        'meta.tag.script.cfml punctuation.separator.key-value',
        'meta.tag.script.cf.cfml punctuation.separator.key-value',
        'meta.class.declaration.cfml punctuation.separator.key-value',
    ]
    if view.match_selector(pos, ','.join(full_scope)):
        return get_previous_word(view, pos)

    return None


def get_function(view, pt):
    if view.match_selector(pt, 'meta.function.cfml'):
        function_scope = 'meta.function.cfml'
    else:
        function_scope = 'meta.function.declaration.cfml'

    function_name_scope = 'entity.name.function.cfml'
    function_region = get_scope_region_containing_point(view, pt, function_scope)
    if function_region:
        function_name_regions = view.find_by_selector(function_name_scope)
        for function_name_region in function_name_regions:
            if function_region.contains(function_name_region):
                return (
                    view.substr(function_name_region).lower(),
                    function_name_region,
                    function_region,
                )
    return None


def get_function_call(view, pt, support=False):
    function_call_scope = 'meta.function-call'
    if support:
        function_call_scope += '.support'
    function_region = get_scope_region_containing_point(view, pt, function_call_scope)
    if function_region:
        function_name_region = view.word(function_region.begin())
        function_args_region = sublime.Region(
            function_name_region.end(), function_region.end()
        )
        return (
            view.substr(function_name_region).lower(),
            function_name_region,
            function_args_region,
        )
    return None


def get_current_function_body(view, pt):
    return get_scope_region_containing_point(view, pt, 'meta.function.body')


def find_variable_assignment(view, position, variable_name):
    regex_prefix = r'(\bvariables\.|\s|\bvar\s+)'
    regex = regex_prefix + variable_name + r'\b\s*=\s*'
    assignments = view.find_all(regex, sublime.FindFlags.IGNORECASE)
    for r in reversed(assignments):
        if r.begin() < position:
            # check for local var assignment
            # and ensure it is in the same function body
            if view.substr(r).lower().startswith('var '):
                function_region = get_current_function_body(view, r.end())
                if not function_region or not function_region.contains(position):
                    continue
            return r
    return None


def get_verified_path(root_path, rel_path):
    """
    Given a valid root path and an unverified relative path out from that root
    path, searches to see if the full path exists. This search is case insensitive,
    but the returned relative path is cased accurately if it is found.
    returns a tuple of (rel_path, exists)
    """
    normalized_root_path = normalize_path(root_path)
    rel_path_elements = normalize_path(rel_path).split('/')
    verified_path_elements = []

    for elem in rel_path_elements:
        dir_map = {
            f.lower(): f
            for f in os.listdir(
                normalized_root_path + '/' + '/'.join(verified_path_elements)
            )
        }
        if elem.lower() not in dir_map:
            return rel_path, False
        verified_path_elements.append(dir_map[elem.lower()])

    return '/'.join(verified_path_elements), True
