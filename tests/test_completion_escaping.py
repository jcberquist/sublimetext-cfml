from component_parser import parse_cfc_file_string

from CFML.src.component_index import completions


def method_completions(source, completion_type='full'):
    functions = parse_cfc_file_string(source)['functions']
    file_map = {key: '/site/model/User.cfc' for key in functions}
    return {
        completion.name: completion
        for completion in completions.make_completions(
            functions, file_map, completion_type
        )
    }


def test_method_names_are_text_in_their_snippets():
    methods = method_completions(
        '<cfcomponent>\n'
        '<cffunction name="a\\b"></cffunction>\n'
        '<cfscript>\n'
        'function $fixNumber(required numeric n) {}\n'
        'function $() {}\n'
        '</cfscript>\n'
        '</cfcomponent>'
    )
    assert methods['$fixNumber'].content == '\\$fixNumber(${1:required numeric n})'
    assert methods['$'].content == '\\$()'
    assert methods['a\\b'].content == 'a\\\\b()'


def test_ordinary_method_snippets_are_unchanged():
    methods = method_completions(
        'component { function find(required numeric id, string s = "x") {} }'
    )
    assert methods['find'].content == (
        'find(${1:required numeric id}${2:, ${3:string s="x"}})'
    )
    assert (
        method_completions(
            'component { function find(required numeric id) {} }', 'basic'
        )['find'].content
        == 'find()'
    )


def test_dot_path_parts_are_text_in_their_snippets():
    from CFML.src.providers.components import (
        dot_path_completions as dotpath_completions,
    )

    def content(path_part, is_cfc):
        part = {'path_part': path_part, 'is_cfc': is_cfc}
        args, kwargs = dotpath_completions.make_completion(part, '', {}, False)
        return args[0], args[2]

    assert content('$lib', False) == ('$lib', '\\$lib.')
    assert content('$Thing', True) == ('$Thing', '\\$Thing')
    assert content('model', False) == ('model', 'model.')


def test_dot_path_constructor_snippets_find_their_component():
    from CFML.src.providers.components import (
        dot_path_completions as dotpath_completions,
    )

    constructor = completions.CfcCompletion(
        'init', '', 'init(${1:numeric id})', '/site/$lib/Thing.cfc', False, False
    )
    part = {'path_part': '$Thing', 'is_cfc': True}
    file_path = '/site/$lib/$Thing.cfc'
    # the cfml_cfc_completions setting is 'basic' in the tests
    project_data = {
        'dot_paths': {'$lib.$thing': {'file_path': file_path}},
        'completions': {file_path: {'basic': {'constructor': constructor}}},
    }
    args, kwargs = dotpath_completions.make_completion(part, '$lib', project_data, True)
    assert args[2] == '\\$Thing(${1:numeric id})'

    # a constructor with another name, as a component's initmethod has
    project_data['completions'][file_path]['basic']['constructor'] = (
        completions.CfcCompletion(
            'setUp', '', 'setUp(${1:numeric id})', file_path, False, False
        )
    )
    args, kwargs = dotpath_completions.make_completion(part, '$lib', project_data, True)
    assert args[2] == '\\$Thing(${1:numeric id})'

    # a component without a constructor
    project_data['completions'][file_path]['basic']['constructor'] = None
    args, kwargs = dotpath_completions.make_completion(part, '$lib', project_data, True)
    assert args[2] == '\\$Thing()'
