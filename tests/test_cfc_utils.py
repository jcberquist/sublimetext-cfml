import json
import re
import types

import pytest
from index_helpers import add_project, git_repo

from CFML.src.providers.components import cfc_utils


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path.as_posix()


def test_a_mapped_file_outside_the_index_resolves_against_the_project_folder(
    tmp_path, project, component_index, monkeypatch
):
    # a project name is a key, not a path to take the folder of
    monkeypatch.setattr(cfc_utils, 'component_index', component_index)
    base = write(tmp_path / 'lib' / 'Base.cfc', 'component {}')
    project_name = project(
        {'mappings': [{'mapping': '/lib', 'path': 'lib'}]}, name='site'
    )
    component_index.reindex_project(project_name)

    view = types.SimpleNamespace(project_name=project_name, file_path=None)
    assert cfc_utils.get_cfc_file_info(view, 'lib.Base') == (base, None)


def view_of(project_name, file_path=None):
    return types.SimpleNamespace(project_name=project_name, file_path=file_path)


@pytest.fixture
def site(tmp_path, index, git_environment, monkeypatch):
    # a git folder with lib ignored, indexed without a project file
    monkeypatch.setattr(cfc_utils, 'component_index', index)
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\ntmp/\n')
    write(site / 'box.json', json.dumps({'installPaths': {'cbauth': 'lib/cbauth'}}))
    write(site / 'handlers' / 'Main.cfc', 'component {}')
    write(site / 'models' / 'User.cfc', 'component { function user() {} }')
    write(site / 'lib' / 'cbauth' / 'models' / 'User.cfc', 'component {}')
    return site


def test_a_dot_path_is_cased_as_the_file_system_has_it(site, index):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    assert cfc_utils.get_cfc_file_info(
        view_of(project_name, main), 'CBAUTH.models.user'
    ) == (
        (site / 'lib' / 'cbauth' / 'models' / 'User.cfc').as_posix(),
        'cbauth.models.User',
    )
    resolution = cfc_utils.resolve_cfc(view_of(project_name, main), 'user')
    assert resolution == cfc_utils.CfcResolution(
        [
            (site / 'models' / 'User.cfc').as_posix(),
            (site / 'lib' / 'cbauth' / 'models' / 'User.cfc').as_posix(),
        ],
        'User',
        True,
    )


def test_a_file_on_disk_next_to_the_view_comes_before_a_guess(site, index):
    # tmp is ignored, so its files are not indexed
    page = write(site / 'tmp' / 'Page.cfc', 'component {}')
    user = write(site / 'tmp' / 'User.cfc', 'component {}')
    project_name = add_project([site])

    assert cfc_utils.get_cfc_file_info(view_of(project_name, page), 'user') == (
        user,
        None,
    )


def test_a_view_with_no_project_finds_a_sibling_on_disk(tmp_path):
    page = write(tmp_path / 'Page.cfc', 'component {}')
    sibling = write(tmp_path / 'sub' / 'Sibling.cfc', 'component {}')

    view = view_of(None, page)
    assert cfc_utils.get_cfc_file_info(view, 'sub.sibling') == (sibling, None)
    assert cfc_utils.get_cfc_file_info(view, 'Missing') == (None, None)
    assert cfc_utils.get_cfc_file_info(view_of(None), 'sub.sibling') == (None, None)


def test_a_configured_project_shows_the_mapped_dot_path(
    tmp_path, project, component_index, monkeypatch
):
    monkeypatch.setattr(cfc_utils, 'component_index', component_index)
    write(tmp_path / 'model' / 'services' / 'Mailer.cfc', 'component {}')
    user = write(tmp_path / 'model' / 'services' / 'UserService.cfc', 'component {}')
    mailer = (tmp_path / 'model' / 'services' / 'Mailer.cfc').as_posix()
    project_name = project(
        {
            'cfc_folders': [{'path': 'model'}],
            'mappings': [{'mapping': '/model', 'path': 'model'}],
        }
    )
    component_index.reindex_project(project_name)

    view = view_of(project_name, user)
    # relative to the file, as through the mapping
    assert cfc_utils.get_cfc_file_info(view, 'mailer') == (
        mailer,
        'model.services.Mailer',
    )
    assert cfc_utils.get_cfc_file_info(view, 'model.services.mailer') == (
        mailer,
        'model.services.Mailer',
    )
    # nothing is guessed
    assert cfc_utils.get_cfc_file_info(view, 'other.Mailer') == (None, None)


def test_the_file_next_to_the_view_comes_before_the_mapping(
    tmp_path, project, component_index, monkeypatch
):
    monkeypatch.setattr(cfc_utils, 'component_index', component_index)
    mapped = write(tmp_path / 'lib' / 'Base.cfc', 'component {}')
    near = write(tmp_path / 'model' / 'lib' / 'Base.cfc', 'component {}')
    user = write(tmp_path / 'model' / 'User.cfc', 'component {}')
    project_name = project(
        {
            'cfc_folders': [{'path': 'model'}, {'path': 'lib'}],
            'mappings': [{'mapping': '/lib', 'path': 'lib'}],
        }
    )
    component_index.reindex_project(project_name)

    assert cfc_utils.get_cfc_file_info(view_of(project_name, user), 'lib.Base') == (
        near,
        'lib.Base',
    )
    assert cfc_utils.get_cfc_file_info(view_of(project_name), 'lib.Base') == (
        mapped,
        'lib.Base',
    )


class Region:
    def __init__(self, begin, end):
        self.a, self.b = begin, end

    def begin(self):
        return self.a

    def end(self):
        return self.b


def constructor_view(project_name, file_path, source, constructor):
    """
    A cfml_view of the source with the position in the constructor call,
    the text that the constructor scope covers.
    """
    begin = source.index(constructor)
    region = Region(begin, begin + len(constructor))
    selector = cfc_utils.constructor_selector

    def in_constructor(pt):
        return region.begin() <= pt < region.end()

    view = types.SimpleNamespace(
        match_selector=lambda pt, s: s == selector and in_constructor(pt),
        scope_name=lambda pt: 'source.cfml ' + (selector if in_constructor(pt) else ''),
        expand_to_scope=lambda pt, s: region,
        substr=lambda r: source[r.begin() : r.end()],
    )
    return types.SimpleNamespace(
        view=view,
        project_name=project_name,
        file_path=file_path,
        position=begin + 5,
    )


def test_goto_from_a_file_opened_alone_finds_a_sibling(tmp_path):
    from CFML.src.providers.components import components

    source = 'component { function f() { return new Sibling(); } }'
    page = write(tmp_path / 'Page.cfc', source)
    sibling = write(tmp_path / 'Sibling.cfc', 'component {}')
    view = constructor_view(None, page, source, 'new Sibling()')

    goto = components.get_goto_cfml_file(view)
    assert goto is not None
    assert goto.file_path == sibling
    assert components.get_method_preview(view) is None
    documentation = components.get_inline_documentation(view, 'inline_doc')
    assert documentation is not None
    assert documentation.doc_regions[0].begin() == source.index('new Sibling()')


def test_a_reference_has_the_other_candidates_and_says_it_is_a_guess(site, index):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()
    source = 'component { function f() { return new User(); } }'
    view = constructor_view(project_name, main, source, 'new User()')

    reference = cfc_utils.find_reference(view, view.position)
    assert reference is not None
    assert reference.file_path == (site / 'models' / 'User.cfc').as_posix()
    assert reference.class_name == 'User'
    assert reference.candidates == (
        (site / 'lib' / 'cbauth' / 'models' / 'User.cfc').as_posix(),
    )
    assert reference.guessed is True

    # a dot path that resolves to one file
    source = 'component { function f() { return new cbauth.models.User(); } }'
    view = constructor_view(project_name, main, source, 'new cbauth.models.User()')
    reference = cfc_utils.find_reference(view, view.position)
    assert reference is not None
    assert reference.class_name == 'cbauth.models.User'
    assert reference.candidates == ()
    assert reference.guessed is False


@pytest.mark.parametrize(
    'text, path',
    [
        ('new User()', 'User'),
        ('new cbauth.models.User(1, new Role())', 'cbauth.models.User'),
        ('new\n\tUser ()', 'User'),
        ('new User', 'User'),
        ('new CFML:models.User()', 'models.User'),
        # Lucee leaves an unprefixed name to the component or the class
        ('new java.util.HashMap()', 'java.util.HashMap'),
        ('new java:User()', None),
        ('new JAVA:java.util.HashMap()', None),
        # typed up to the cursor
        ('new ', ''),
        ('new models.', 'models.'),
        ('new cfml:', ''),
        ('new java:', None),
        ('new "../models/User"()', None),
        ('new component extends="Base" {', None),
    ],
)
def test_the_path_of_a_constructor(text, path):
    assert cfc_utils.get_constructor_path(text) == path


def test_a_cfml_prefix_is_not_part_of_the_reference(site, index):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()
    source = 'component { function f() { return new cfml:cbauth.models.User(); } }'
    view = constructor_view(project_name, main, source, 'new cfml:cbauth.models.User()')

    reference = cfc_utils.find_reference(view, view.position)
    assert reference is not None
    assert reference.class_name == 'cbauth.models.User'
    assert reference.guessed is False


def test_a_java_class_is_not_a_component(site, index):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()
    source = 'component { function f() { return new java:User(); } }'
    view = constructor_view(project_name, main, source, 'new java:User()')

    assert cfc_utils.find_reference(view, view.position) is None


def dot_view(project_name, file_path, source, constructor):
    """A cfml_view after the last dot of the source."""
    cfml_view = constructor_view(project_name, file_path, source, constructor)
    cfml_view.prefix_start = source.rindex('.') + 1
    name = re.search(r'(\w*)\W*$', source[: cfml_view.prefix_start - 1]).group(1)
    cfml_view.dot_context = [types.SimpleNamespace(name=name, is_function=False)]
    return cfml_view


def test_a_method_after_a_constructor_is_of_its_component(site, index, monkeypatch):
    from CFML.src.providers.components import dot_path_completions

    monkeypatch.setattr(dot_path_completions, 'component_index', index)
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    def triggers(source, constructor):
        view = dot_view(project_name, main, source, constructor)
        completions = dot_path_completions.get_dot_completions(view)
        return completions and [args[0] for args, kwargs in completions]

    assert triggers('new cfml:models.User().', 'new cfml:models.User()') == ['user']
    assert triggers('new java:User().', 'new java:User()') is None

    # nor a dot in its dot path or its arguments, which is not looked up
    # as a variable either
    assignments = []
    monkeypatch.setattr(
        cfc_utils,
        'find_cfc_by_var_assignment',
        lambda view, pt, name: assignments.append(name) or (None,) * 5,
    )
    assert triggers('new models.', 'new models.') is None
    assert triggers('new models.User(user.)', 'new models.User(user.)') is None
    assert assignments == []
