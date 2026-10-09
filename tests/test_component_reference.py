import types

import pytest

from CFML.src import component_reference, minihtml
from CFML.src.cfml_view import GotoCfmlFile
from CFML.src.component_reference import ComponentReference

from test_component_index import index_site

REGIONS = [(0, 5)]


@pytest.fixture
def site(tmp_path, project, component_index, monkeypatch):
    """A cfml_view in a project with model/Child.cfc, which extends Base.cfc."""
    monkeypatch.setattr(component_reference, 'component_index', component_index)
    project_name, child = index_site(tmp_path, project, component_index)
    cfml_view = types.SimpleNamespace(view=object(), project_name=project_name)
    base = (tmp_path / 'model' / 'Base.cfc').as_posix()
    return types.SimpleNamespace(cfml_view=cfml_view, child=child, base=base)


def reference(file_path, function_name=None, method_class_name=None):
    return ComponentReference(
        file_path, 'model.Child', function_name, REGIONS, method_class_name
    )


def header(result):
    return result.content.header


def test_goto_a_component_is_its_file(site):
    goto = component_reference.get_goto_cfml_file(site.cfml_view, reference(site.child))
    assert goto == GotoCfmlFile(site.child, None, component_reference.PRIORITY)


def test_goto_an_inherited_method_is_the_file_that_declares_it(site):
    goto = component_reference.get_goto_cfml_file(
        site.cfml_view, reference(site.child, 'inherited')
    )
    assert goto == GotoCfmlFile(site.base, 'inherited', component_reference.PRIORITY)


def test_no_goto_for_a_method_the_component_does_not_have(site):
    goto = component_reference.get_goto_cfml_file(
        site.cfml_view, reference(site.child, 'missing')
    )
    assert goto is None


def test_method_doc_names_the_component_and_the_method(site):
    doc = component_reference.get_inline_documentation(
        site.cfml_view, reference(site.child, 'own', 'Child')
    )
    assert doc.doc_regions == REGIONS
    assert '>Child</span>.' in header(doc)
    assert '>own</span>()' in header(doc)


def test_component_doc_for_a_method_the_component_does_not_have(site):
    doc = component_reference.get_inline_documentation(
        site.cfml_view, reference(site.child, 'missing', 'Child')
    )
    assert '>model.Child</span>' in header(doc)
    assert 'missing' not in header(doc)


def test_no_docs_for_a_component_that_is_not_indexed(site, tmp_path):
    other = reference((tmp_path / 'other' / 'Other.cfc').as_posix(), 'own')
    assert component_reference.get_inline_documentation(site.cfml_view, other) is None
    assert component_reference.get_method_preview(site.cfml_view, other) is None
    assert component_reference.get_goto_cfml_file(site.cfml_view, other) is None


def test_no_method_preview_without_a_method_of_the_component(site):
    for function_name in [None, 'missing']:
        preview = component_reference.get_method_preview(
            site.cfml_view, reference(site.child, function_name)
        )
        assert preview is None


def test_completion_doc_is_for_the_call_at_the_position(site):
    site.cfml_view.function_call_params = types.SimpleNamespace(
        function_name='inherited', named_params=False, current_index=0, params=[]
    )
    doc = component_reference.get_completion_doc(
        site.cfml_view, reference(site.child, None, 'Child')
    )
    assert '>Child</span>.' in header(doc)
    assert '>inherited</span>()' in header(doc)

    site.cfml_view.function_call_params.function_name = 'missing'
    doc = component_reference.get_completion_doc(site.cfml_view, reference(site.child))
    assert doc is None


# the docs of the site as they were before references had candidates, with
# the paths relative to the folder of the project's window
COMPONENT_DOC_BODY = (
    '<div class="path"><strong>path</strong>: <a href="__go_to_component">'
    'model/Child.cfc</a></div>\n'
    '<div class="card">\n'
    '    <div class="card-header card-header-empty"><strong>extends: '
    '<span class="entity-other-inherited-class">model.Base</span></strong></div>\n'
    '    </div>\n'
    '<h2>Public methods</h2>\n'
    '<div class="card">\n'
    '    <div class="card-header"><a class="plain-link" href="inherited">'
    '<span class="entity-name-function">inherited</span>()</a></div>\n'
    '    <div class="card-body"><small><em>(from Base.cfc)</em></small></div>\n'
    '</div>\n'
    '\n'
    '<div class="card">\n'
    '    <div class="card-header card-header-empty"><a class="plain-link" href="own">'
    '<span class="entity-name-function">own</span>()</a></div>\n'
    '    </div>\n'
)
METHOD_DOC_HEADER = (
    '<span class="storage-modifier">public</span> '
    '<span class="entity-name-class">Child</span>.'
    '<span class="entity-name-function">inherited</span>()'
)
METHOD_DOC_BODY = (
    '<div class="path"><strong>path</strong>: <a href="inherited">'
    'model/Base.cfc</a></div>'
)


class RecordingWindow:
    def __init__(self):
        self.opened = []
        self.commands = []

    def open_file(self, path, flags=0):
        self.opened.append(path)

    def run_command(self, name, args):
        self.commands.append((name, args))


@pytest.fixture
def docs(site, monkeypatch):
    # no method previews, which need a view to highlight the code in
    monkeypatch.setattr(component_reference.utils, 'get_setting', lambda key: False)
    site.window = RecordingWindow()
    site.cfml_view.view = types.SimpleNamespace(window=lambda: site.window)
    return site


def doc_of(site, file_path, function_name=None, candidates=(), guessed=False):
    reference = ComponentReference(
        file_path,
        'model.Child',
        function_name,
        REGIONS,
        'Child',
        candidates=candidates,
        guessed=guessed,
    )
    doc = component_reference.get_inline_documentation(site.cfml_view, reference)
    assert doc is not None
    return doc


def test_docs_without_candidates_are_as_they_were(docs):
    doc = doc_of(docs, docs.child)
    assert doc.content.header == '<span class="entity-name-class">model.Child</span>'
    assert doc.content.body == COMPONENT_DOC_BODY

    doc = doc_of(docs, docs.child, 'inherited')
    assert doc.content.header == METHOD_DOC_HEADER
    assert doc.content.body == METHOD_DOC_BODY


def test_a_guess_says_so_under_the_path(docs):
    note = '<div class="path"><small><em>matched by name</em></small></div>'

    doc = doc_of(docs, docs.child, guessed=True)
    path = COMPONENT_DOC_BODY.split('\n', 1)[0]
    assert doc.content.body.startswith(path + note + '\n<div class="card">')

    doc = doc_of(docs, docs.child, 'inherited', guessed=True)
    assert doc.content.body == METHOD_DOC_BODY + note


def test_other_candidates_are_links_under_the_path(docs, tmp_path):
    lib = (tmp_path / 'lib' / 'Child.cfc').as_posix()
    other = (tmp_path / 'other' / 'Child.cfc').as_posix()

    doc = doc_of(docs, docs.child, 'inherited', (lib, other))
    assert doc.content.body.endswith(
        '<div class="path"><small><em>also:</em> '
        '<a href="__candidate_0">lib/Child</a>, '
        '<a href="__candidate_1">other/Child</a></small></div>'
    )

    doc = doc_of(docs, docs.child, 'inherited', (lib,), guessed=True)
    assert doc.content.body.endswith(
        '<div class="path"><small><em>matched by name; also:</em> '
        '<a href="__candidate_0">lib/Child</a></small></div>'
    )


def test_at_most_five_candidates_are_named(docs, tmp_path):
    def candidates(count):
        return tuple(
            (tmp_path / f'c{index}' / 'Child.cfc').as_posix() for index in range(count)
        )

    doc = doc_of(docs, docs.child, candidates=candidates(5))
    assert doc.content.body.count('href="__candidate_') == 5
    assert ' more' not in doc.content.body

    doc = doc_of(docs, docs.child, candidates=candidates(7))
    assert doc.content.body.count('href="__candidate_') == 4
    assert '<a href="__candidate_3">c3/Child</a> and 3 more</small>' in (
        doc.content.body
    )


def test_a_candidate_path_is_escaped(docs, tmp_path):
    weird = (tmp_path / 'a&b<c' / 'Child.cfc').as_posix()
    doc = doc_of(docs, docs.child, candidates=(weird,), guessed=True)
    assert '<a href="__candidate_0">a&amp;b&lt;c/Child</a>' in doc.content.body
    assert 'a&b' not in doc.content.body


def test_a_candidate_link_opens_its_component(docs, tmp_path):
    lib = (tmp_path / 'lib' / 'Child.cfc').as_posix()
    doc = doc_of(docs, docs.child, candidates=(docs.base, lib))
    assert doc.on_navigate is not None

    doc.on_navigate('__candidate_1')
    doc.on_navigate('__candidate_0')
    # the doc's own links work as before
    doc.on_navigate('__go_to_component')
    assert docs.window.opened == [lib, docs.base, docs.child]


def test_a_candidate_link_of_a_method_doc_opens_the_method(docs, tmp_path):
    lib = (tmp_path / 'lib' / 'Child.cfc').as_posix()
    doc = doc_of(docs, docs.child, 'inherited', (docs.base, lib))
    assert doc.on_navigate is not None

    doc.on_navigate('__candidate_0')
    assert docs.window.commands == [
        (
            'cfml_navigate_to_method',
            {'file_path': docs.base, 'href': 'inherited'},
        )
    ]
    # a candidate that is not indexed has no method to open at
    doc.on_navigate('__candidate_1')
    assert docs.window.opened == [lib]


def test_completion_docs_and_previews_are_of_the_best_candidate(docs):
    docs.cfml_view.function_call_params = types.SimpleNamespace(
        function_name='inherited', named_params=False, current_index=0, params=[]
    )
    alone = ComponentReference(docs.child, 'Child', None, REGIONS)
    several = alone._replace(candidates=(docs.base,), guessed=True)
    assert component_reference.get_completion_doc(
        docs.cfml_view, several
    ) == component_reference.get_completion_doc(docs.cfml_view, alone)


def test_tell_apart_is_the_one_of_the_variable_names():
    from CFML.src.providers.components import cfcs

    for file_paths in [
        ['/site/app/Env.cfc', '/site/lib/testbox/system/util/Env.cfc'],
        ['/site/a/models/User.cfc', '/site/b/models/User.cfc', '/site/User.cfc'],
        ['/site/a/User.cfc', '/site/A/user.cfc'],
    ]:
        assert component_reference.tell_apart(file_paths) == cfcs.tell_apart(file_paths)


def test_doc_paths_are_relative_to_the_folders_of_the_project(
    docs, tmp_path, monkeypatch
):
    from CFML.src import project_files
    from CFML.src.providers.components import dot_path_documentation

    # tmp_path can be under the home folder, which would be shown as ~
    monkeypatch.setattr(project_files, 'HOME', None)

    assert component_reference.get_project_folders(docs.cfml_view) == (
        tmp_path.as_posix(),
    )
    other = (tmp_path / 'other' / 'Other.cfc').as_posix()
    reference = ComponentReference(other, 'other.Other', None, REGIONS)
    # a component that is not indexed has its path shown all the same
    doc = dot_path_documentation.get_inline_documentation(docs.cfml_view, reference)
    assert doc is not None
    assert '<a href="__go_to_component">other/Other.cfc</a>' in doc.content.body

    # a view that is in no project shows the whole path, cut short if long
    docs.cfml_view.project_name = None
    assert component_reference.get_project_folders(docs.cfml_view) == ()
    doc = dot_path_documentation.get_inline_documentation(docs.cfml_view, reference)
    assert doc is not None
    shown = minihtml.escape_text(minihtml.shorten_path(other))
    assert '<a href="__go_to_component">' + shown + '</a>' in doc.content.body
    assert shown.startswith('/') and shown.endswith('/other/Other.cfc')
