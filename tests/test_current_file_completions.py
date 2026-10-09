import types

from CFML.src.providers.current_file import completions

from test_component_index import write


def super_completions(component_index, monkeypatch, project_name, file_path, extends):
    # the names of the completions after `super.` in the given file
    monkeypatch.setattr(completions, 'component_index', component_index)
    monkeypatch.setattr(
        completions, 'to_completion_item', lambda completion: completion.name
    )
    cfml_view = types.SimpleNamespace(
        dot_context=[types.SimpleNamespace(name='super', is_function=False)],
        file_path=file_path,
        project_name=project_name,
        view_metadata={'extends': extends},
    )
    return completions.get_dot_completions(cfml_view)


def test_super_completions_are_those_of_the_component_next_to_it(
    tmp_path, project, component_index, monkeypatch
):
    # a mapping has another component under the dot path `Base`
    write(tmp_path / 'lib' / 'Base.cfc', 'component { function mapped() {} }')
    write(tmp_path / 'model' / 'Base.cfc', 'component { function sibling() {} }')
    child = write(tmp_path / 'model' / 'Child.cfc', 'component extends="Base" {}')
    project_name = project(
        {
            'cfc_folders': [{'path': 'lib'}, {'path': 'model'}],
            'mappings': [{'mapping': '/', 'path': 'lib'}],
        }
    )
    component_index.reindex_project(project_name)

    assert super_completions(
        component_index, monkeypatch, project_name, child, 'Base'
    ) == ['sibling']


def test_super_completions_of_an_unsaved_buffer_come_from_the_dot_path(
    tmp_path, project, component_index, monkeypatch
):
    write(tmp_path / 'lib' / 'Base.cfc', 'component { function mapped() {} }')
    project_name = project(
        {
            'cfc_folders': [{'path': 'lib'}],
            'mappings': [{'mapping': '/', 'path': 'lib'}],
        }
    )
    component_index.reindex_project(project_name)

    assert super_completions(
        component_index, monkeypatch, project_name, None, 'Base'
    ) == ['mapped']


def test_the_functions_of_the_file_are_completed(settings):
    # the file's own functions, in script and after `this.`, come from the
    # completions built of its metadata
    from test_documentation_escaping import extended

    cfml_view = types.SimpleNamespace(
        dot_context=[types.SimpleNamespace(name='this', is_function=False)],
        view_metadata=extended('component { function init() {} function run(x) {} }'),
    )
    for found in [
        completions.get_script_completions(cfml_view),
        completions.get_dot_completions(cfml_view),
    ]:
        # a stand-in CompletionItem is its (args, kwargs); the name is first
        assert sorted(args[0] for args, kwargs in found) == ['init', 'run']
