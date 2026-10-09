import types

from CFML.src.component_reference import ComponentReference
from CFML.src.providers.current_file import documentation

from test_component_index import index_site


def hover_super(project_name, file_path, extends):
    # a cfml_view with the caret on `super` in the given file
    view = types.SimpleNamespace(
        match_selector=lambda pt, selector: selector == 'variable.language.super.cfml',
        word=lambda pt: (pt, pt + 5),
    )
    cfml_view = types.SimpleNamespace(
        view=view,
        file_path=file_path,
        project_name=project_name,
        view_metadata={'extends': extends},
    )
    return documentation.get_cfc_info(cfml_view, 0)


def test_super_doc_is_the_extended_component(
    tmp_path, project, component_index, monkeypatch
):
    monkeypatch.setattr(documentation, 'component_index', component_index)
    project_name, child = index_site(tmp_path, project, component_index)

    extended_meta, file_path, header, regions = hover_super(
        project_name, child, 'model.Base'
    )
    assert file_path == (tmp_path / 'model' / 'Base.cfc').as_posix()
    assert header == 'model.Base'
    assert list(extended_meta['functions']) == ['inherited']


def test_super_doc_shows_the_path_relative_to_the_project_folder(
    tmp_path, project, component_index, monkeypatch
):
    monkeypatch.setattr(documentation, 'component_index', component_index)
    project_name, child = index_site(tmp_path, project, component_index)
    view = types.SimpleNamespace(
        match_selector=lambda pt, selector: selector == 'variable.language.super.cfml',
        word=lambda pt: (pt, pt + 5),
    )
    cfml_view = types.SimpleNamespace(
        view=view,
        position=0,
        file_path=child,
        project_name=project_name,
        view_metadata={'extends': 'model.Base'},
    )
    doc = documentation.get_inline_documentation(cfml_view, None)
    assert doc is not None
    assert '<a href="__go_to_component">model/Base.cfc</a>' in doc.content.body


def test_no_super_doc_in_a_component_that_extends_nothing(
    tmp_path, project, component_index, monkeypatch
):
    monkeypatch.setattr(documentation, 'component_index', component_index)
    project_name, _child = index_site(tmp_path, project, component_index)
    base = (tmp_path / 'model' / 'Base.cfc').as_posix()

    assert hover_super(project_name, base, None) is None


def test_only_an_inherited_function_is_looked_up_in_the_index():
    file_map = {'inherited': '/site/Base.cfc', 'own': '/site/Child.cfc'}
    cfml_view = types.SimpleNamespace(file_path='/site/Child.cfc')

    def inherited_reference(function_name):
        function_info = documentation.FunctionInfo(
            {'function_file_map': file_map}, function_name, function_name, []
        )
        return documentation.get_inherited_reference(cfml_view, function_info)

    assert inherited_reference('inherited') == ComponentReference(
        '/site/Base.cfc', None, 'inherited', []
    )
    assert inherited_reference('own') is None

    # the functions of a buffer that has not been saved have no file
    file_map['own'] = ''
    cfml_view.file_path = None
    assert inherited_reference('own') is None
