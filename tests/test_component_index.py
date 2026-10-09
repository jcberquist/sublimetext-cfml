import pytest

from CFML.src.project_watcher import project_watcher

BASE = 'component { function inherited() {} }'
CHILD = 'component extends="model.Base" { function own() {} }'


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path.as_posix()


def completion_names(index, project_name, file_path):
    completions = index.get_completions_by_file_path(project_name, file_path)
    return [completion.name for completion in completions['functions']]


def index_site(tmp_path, project, component_index, mapping='/model'):
    write(tmp_path / 'model' / 'Base.cfc', BASE)
    child = write(tmp_path / 'model' / 'Child.cfc', CHILD)
    project_name = project(
        {
            'cfc_folders': [{'path': 'model'}],
            'mappings': [{'mapping': mapping, 'path': 'model'}],
        }
    )
    component_index.reindex_project(project_name)
    return project_name, child


def test_first_index_resolves_inherited_completions(tmp_path, project, component_index):
    project_name, child = index_site(tmp_path, project, component_index)
    assert completion_names(component_index, project_name, child) == [
        'inherited',
        'own',
    ]


def test_mapping_change_resolves_against_the_new_mappings(
    tmp_path, project, component_index
):
    project_name, child = index_site(tmp_path, project, component_index, mapping='/old')
    assert completion_names(component_index, project_name, child) == ['own']

    project_data = project_watcher.get_project_data(project_name)
    project_data['mappings'] = [{'mapping': '/model', 'path': 'model'}]
    component_index.project_event_handler('project_updated', project_name)
    assert completion_names(component_index, project_name, child) == [
        'inherited',
        'own',
    ]


def index_folders(tmp_path, project, component_index, mappings=None):
    # Base.cfc in model, in model/admin and in lib, each with its own function
    for folder in ['model', 'model/admin', 'lib']:
        name = folder.replace('/', '_')
        write(
            tmp_path / folder / 'Base.cfc', 'component { function ' + name + '() {} }'
        )
    project_data = {'cfc_folders': [{'path': 'model'}, {'path': 'lib'}]}
    if mappings is not None:
        project_data['mappings'] = mappings
    project_name = project(project_data)
    component_index.reindex_project(project_name)
    return project_name


def inherited_from(index, project_name, file_path, extends):
    # the function names a component at file_path gets from what it extends
    source = 'component extends="' + extends + '" {}'
    metadata = index.parser.parse_file(write(file_path, source))
    extended = index.extend_metadata(project_name, file_path.as_posix(), metadata)
    return list(extended['functions'])


def test_extends_resolves_in_the_folder_of_the_component_without_mappings(
    tmp_path, project, component_index
):
    project_name = index_folders(tmp_path, project, component_index)
    model = tmp_path / 'model'

    def inherited(file_path, extends):
        return inherited_from(component_index, project_name, file_path, extends)

    assert inherited(model / 'Child.cfc', 'Base') == ['model']
    assert inherited(model / 'admin' / 'Child.cfc', 'Base') == ['model_admin']
    # dots are folders, and case does not matter
    assert inherited(model / 'Child.cfc', 'admin.Base') == ['model_admin']
    assert inherited(model / 'Child.cfc', 'ADMIN.base') == ['model_admin']
    # nothing reaches another folder
    assert inherited(model / 'Child.cfc', 'lib.Base') == []
    assert inherited(model / 'Child.cfc', 'model.Base') == []
    assert inherited(model / 'Child.cfc', 'Missing') == []


def test_extends_resolves_in_the_folder_before_the_mappings(
    tmp_path, project, component_index
):
    mappings = [{'mapping': '/', 'path': 'model'}, {'mapping': '/lib', 'path': 'lib'}]
    project_name = index_folders(tmp_path, project, component_index, mappings)
    model = tmp_path / 'model'

    def inherited(file_path, extends):
        return inherited_from(component_index, project_name, file_path, extends)

    # /Base is model/Base.cfc, but the one next to the component comes first
    assert inherited(model / 'admin' / 'Child.cfc', 'Base') == ['model_admin']
    assert inherited(model / 'Child.cfc', 'Base') == ['model']
    # through a mapping, from any folder
    assert inherited(model / 'admin' / 'Child.cfc', 'admin.Base') == ['model_admin']
    assert inherited(model / 'admin' / 'Child.cfc', 'lib.Base') == ['lib']
    assert inherited(tmp_path / 'lib' / 'Child.cfc', 'admin.Base') == ['model_admin']


def test_extends_in_an_unsaved_buffer_resolves_through_the_mappings(
    tmp_path, project, component_index
):
    mappings = [{'mapping': '/lib', 'path': 'lib'}]
    project_name = index_folders(tmp_path, project, component_index, mappings)
    lib_base = (tmp_path / 'lib' / 'Base.cfc').as_posix()

    assert component_index.resolve_path(project_name, '', 'lib.Base') == lib_base
    # it has no folder to look in
    assert component_index.resolve_path(project_name, '', 'Base') is None
    assert component_index.resolve_path(project_name, '', None) is None


def test_added_file_is_resolved_in_the_folder_while_rebuilding(
    tmp_path, project, component_index
):
    child = write(
        tmp_path / 'model' / 'Child.cfc',
        'component extends="Base" { function own() {} }',
    )
    project_name = project({'cfc_folders': [{'path': 'model'}]})
    component_index.reindex_project(project_name)
    assert completion_names(component_index, project_name, child) == ['own']

    # the completions are built before the data with Base.cfc is published
    base = write(tmp_path / 'model' / 'Base.cfc', BASE)
    component_index.project_event_handler('project_file_updated', project_name, base)
    assert completion_names(component_index, project_name, child) == [
        'inherited',
        'own',
    ]

    (tmp_path / 'model' / 'Base.cfc').unlink()
    component_index.project_event_handler('project_file_removed', project_name, base)
    assert completion_names(component_index, project_name, child) == ['own']


def test_file_update_keeps_the_previews_of_unchanged_files(
    tmp_path, project, component_index
):
    project_name, child = index_site(tmp_path, project, component_index)
    base = (tmp_path / 'model' / 'Base.cfc').as_posix()
    component_index.get_cache_by_file_path(project_name, base)['inherited'] = 1
    component_index.get_cache_by_file_path(project_name, child)['own'] = 1

    write(tmp_path / 'model' / 'Child.cfc', CHILD.replace('own', 'renamed'))
    component_index.project_event_handler('project_file_updated', project_name, child)
    assert component_index.get_cache_by_file_path(project_name, base) == {
        'inherited': 1
    }
    assert component_index.get_cache_by_file_path(project_name, child) == {}
    assert completion_names(component_index, project_name, child) == [
        'inherited',
        'renamed',
    ]


def test_file_update_rebuilds_the_completions_of_what_extends_it(
    tmp_path, project, component_index
):
    project_name, child = index_site(tmp_path, project, component_index)
    grandchild = write(
        tmp_path / 'model' / 'GrandChild.cfc', 'component extends="Child" {}'
    )
    other = write(tmp_path / 'model' / 'Other.cfc', 'component { function x() {} }')
    for file_path in [grandchild, other]:
        component_index.project_event_handler(
            'project_file_updated', project_name, file_path
        )
    published = component_index.data[project_name]['completions']

    base = write(tmp_path / 'model' / 'Base.cfc', BASE.replace('inherited', 'moved'))
    component_index.project_event_handler('project_file_updated', project_name, base)
    assert completion_names(component_index, project_name, child) == ['moved', 'own']
    assert completion_names(component_index, project_name, grandchild) == [
        'moved',
        'own',
    ]
    # the completions of a component that does not extend it are kept
    completions = component_index.data[project_name]['completions']
    assert completions[other] is published[other]
    assert completions[base] is not published[base]


def test_file_update_replaces_the_published_data(tmp_path, project, component_index):
    project_name, child = index_site(tmp_path, project, component_index)
    published = component_index.data[project_name]

    write(tmp_path / 'model' / 'Child.cfc', CHILD.replace('own', 'renamed'))
    component_index.project_event_handler('project_file_updated', project_name, child)
    # a reader still holding the old data sees all of it unchanged
    assert component_index.data[project_name] is not published
    assert list(published['index'][child]['functions']) == ['own']


def test_files_in_a_sibling_folder_with_the_same_prefix_are_not_indexed(
    tmp_path, project, component_index
):
    project_name, child = index_site(tmp_path, project, component_index)
    other = write(tmp_path / 'model-old' / 'Other.cfc', BASE)

    assert component_index.in_folders(project_name, child)
    assert not component_index.in_folders(project_name, other)
    component_index.project_event_handler('project_file_updated', project_name, other)
    assert other not in component_index.get_project_index(project_name)


def test_only_components_are_indexed_on_save(tmp_path, project, component_index):
    project_name, child = index_site(tmp_path, project, component_index)
    page = write(tmp_path / 'model' / 'page.cfm', '<cfoutput>hi</cfoutput>')
    script = write(tmp_path / 'model' / 'app.js', 'function f() {}')

    for file_path in [page, script]:
        component_index.project_event_handler(
            'project_file_updated', project_name, file_path
        )
    assert sorted(component_index.get_project_index(project_name)) == [
        (tmp_path / 'model' / 'Base.cfc').as_posix(),
        child,
    ]
    assert 'model.page' not in component_index.get_dot_paths(project_name)


def test_a_file_that_cannot_be_read_is_removed_on_save(
    tmp_path, project, component_index
):
    project_name, child = index_site(tmp_path, project, component_index)
    base = tmp_path / 'model' / 'Base.cfc'
    # a Windows-1252 file is not valid UTF-8
    base.write_bytes(b'component { function caf\xe9() {} }')

    component_index.project_event_handler(
        'project_file_updated', project_name, base.as_posix()
    )
    assert base.as_posix() not in component_index.get_project_index(project_name)
    assert 'model.base' not in component_index.get_dot_paths(project_name)
    assert completion_names(component_index, project_name, child) == ['own']

    # and the next rebuild works
    component_index.project_event_handler('project_updated', project_name)
    assert completion_names(component_index, project_name, child) == ['own']


def test_a_failed_build_leaves_the_published_data(
    tmp_path, project, component_index, monkeypatch
):
    project_name, child = index_site(tmp_path, project, component_index)
    published = component_index.data[project_name]
    monkeypatch.setattr(component_index, 'index_file', lambda file_path: {})

    with pytest.raises(KeyError):
        component_index.project_event_handler(
            'project_file_updated', project_name, child
        )
    assert component_index.data[project_name] is published
    assert completion_names(component_index, project_name, child) == [
        'inherited',
        'own',
    ]


def test_listeners_are_given_each_published_snapshot(
    tmp_path, project, component_index
):
    published = []
    component_index.subscribe(lambda *args: published.append(args))
    project_name, child = index_site(tmp_path, project, component_index)
    assert published == [(project_name, component_index.data[project_name])]

    write(tmp_path / 'model' / 'Child.cfc', CHILD.replace('own', 'renamed'))
    component_index.project_event_handler('project_file_updated', project_name, child)
    assert published[1] == (project_name, component_index.data[project_name])
    assert published[1][1] is not published[0][1]
    assert list(published[1][1]['index'][child]['functions']) == ['renamed']

    component_index.project_event_handler('project_removed', project_name)
    assert published[2] == (project_name, None)
    assert project_name not in component_index.data


def test_the_constructor_is_the_init_method_or_init(tmp_path, project, component_index):
    project_name, child = index_site(tmp_path, project, component_index)
    setup = write(tmp_path / 'model' / 'Setup.cfc', 'component initmethod="setUp" {}')
    component_index.project_event_handler('project_file_updated', project_name, setup)

    def is_init_method(file_path, function_name):
        return component_index.is_init_method(project_name, file_path, function_name)

    assert is_init_method(child, 'init')
    assert not is_init_method(child, 'setup')
    assert is_init_method(setup, 'setup')
    assert not is_init_method(setup, 'init')

    # a component that is not indexed, or was not found
    assert is_init_method((tmp_path / 'other' / 'Other.cfc').as_posix(), 'init')
    assert is_init_method(None, 'init')
    assert not is_init_method(None, 'setup')


def test_the_constructor_completion_is_that_of_the_init_method(
    tmp_path, project, component_index
):
    project_name, child = index_site(tmp_path, project, component_index)
    setup = write(
        tmp_path / 'model' / 'Setup.cfc',
        'component initmethod="setUp" { function init() {} function setUp(a) {} }',
    )
    plain = write(tmp_path / 'model' / 'Plain.cfc', 'component { function init(b) {} }')
    for file_path in [setup, plain]:
        component_index.project_event_handler(
            'project_file_updated', project_name, file_path
        )

    def constructor(file_path):
        completions = component_index.data[project_name]['completions'][file_path]
        return completions['required']['constructor']

    assert constructor(setup).content == 'setUp(${1:a})'
    assert constructor(plain).content == 'init(${1:b})'
    assert constructor(child) is None


def test_clearing_the_cache_parses_the_open_projects_again(
    tmp_path, project, component_index, monkeypatch, capsys
):
    from CFML.src.component_parser import cfml_components

    project_name, child = index_site(tmp_path, project, component_index)
    published = component_index.data[project_name]

    parsed = []
    parse = cfml_components.parse_cfc_file_string

    def parse_and_count(file_string):
        parsed.append(file_string)
        return parse(file_string)

    monkeypatch.setattr(cfml_components, 'parse_cfc_file_string', parse_and_count)

    # indexing again reads the cache
    component_index.reindex_project(project_name)
    assert parsed == []

    capsys.readouterr()
    component_index.clear_cache()
    assert len(parsed) == 2
    assert component_index.data[project_name] is not published
    assert completion_names(component_index, project_name, child) == [
        'inherited',
        'own',
    ]
    assert 'cache cleared' in capsys.readouterr().out


def test_relative_paths_resolve_against_the_folder_of_the_project_file(
    tmp_path, project, component_index
):
    # a project name is a key, not a path to take the folder of
    write(tmp_path / 'model' / 'Base.cfc', BASE)
    child = write(tmp_path / 'model' / 'Child.cfc', CHILD)
    project_name = project(
        {
            'cfc_folders': [{'path': 'model'}],
            'mappings': [{'mapping': '/model', 'path': 'model'}],
        },
        name='site',
    )
    component_index.reindex_project(project_name)

    assert completion_names(component_index, project_name, child) == [
        'inherited',
        'own',
    ]
    assert component_index.get_folder_mapping(project_name, child) == 'model'
