import types

from CFML.src.providers.components import cfcs
from CFML.src.utils import Symbol


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_cfcs_in_a_sibling_folder_with_the_same_prefix(
    tmp_path, project, component_index, monkeypatch
):
    # the provider reads the package's component index instance
    monkeypatch.setattr(cfcs, 'component_index', component_index)
    monkeypatch.setattr(cfcs, 'projects', {})
    write(tmp_path / 'model' / 'User.cfc', 'component {}')
    write(tmp_path / 'model-old' / 'Legacy.cfc', 'component {}')
    project_name = project(
        {
            'cfc_folders': [
                {'path': 'model', 'variable_names': ['{cfc}Service']},
                {'path': 'model-old'},
            ]
        }
    )
    component_index.reindex_project(project_name)

    cfcs.build_project_cfcs(project_name, component_index.data[project_name])
    assert cfcs.get_cfc_list(project_name) == ['UserService']


def test_cfc_folders_resolve_against_the_folder_of_the_project_file(
    tmp_path, project, component_index, monkeypatch
):
    # a project name is a key, not a path to take the folder of
    monkeypatch.setattr(cfcs, 'component_index', component_index)
    monkeypatch.setattr(cfcs, 'projects', {})
    write(tmp_path / 'model' / 'User.cfc', 'component {}')
    project_name = project(
        {'cfc_folders': [{'path': 'model', 'variable_names': ['{cfc}Service']}]},
        name='site',
    )
    component_index.reindex_project(project_name)

    cfcs.build_project_cfcs(project_name, component_index.data[project_name])
    assert cfcs.get_cfc_list(project_name) == ['UserService']


def region(begin, end):
    return types.SimpleNamespace(begin=lambda: begin, end=lambda: end)


def test_a_cfc_is_found_by_a_variable_name_or_a_getter(monkeypatch):
    monkeypatch.setattr(cfcs, 'projects', {'site': {'userservice': {}}})

    # variables.userService.
    variable = [
        Symbol('userservice', False, None, None, region(10, 21)),
        Symbol('variables', False, None, None, region(0, 9)),
    ]
    assert cfcs.find_cfc_in_dot_context('site', variable) == ('userservice', (10, 21))

    # getUserService().
    getter_region = region(0, 14)
    getter = [Symbol('getuserservice', True, getter_region, None, getter_region)]
    assert cfcs.search_dot_context_for_cfc('site', getter) is None
    assert cfcs.find_cfc_in_dot_context('site', getter) == (
        'userservice',
        getter_region,
    )

    other = [Symbol('other', False, None, None, region(0, 5))]
    assert cfcs.find_cfc_in_dot_context('site', other) is None
