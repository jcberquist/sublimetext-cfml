import collections
import io
import sys
import types
import urllib.error
from unittest import mock

import pytest
from component_parser import parse_cfc_file_string

from CFML.src import minihtml
from CFML.src.component_index import documentation

FILE_PATH = '/site/model/User.cfc'


def extended(source, file_path=FILE_PATH):
    # the metadata of a component that extends nothing, as the component
    # index hands it to the docs
    meta = parse_cfc_file_string(source)
    meta['function_file_map'] = {key: file_path for key in meta['functions']}
    meta['property_file_map'] = {key: file_path for key in meta['properties']}
    return meta


def tag_function(name='f', returntype=None, access='public', parameters=()):
    # the metadata of one function; tag attributes can carry any text
    meta = {
        'functions': {
            name.lower(): {
                'name': name,
                'meta': {
                    'access': access,
                    'returntype': returntype,
                    'parameters': [
                        {'required': False, 'type': None, 'default': None, **p}
                        for p in parameters
                    ],
                },
                'implicit': False,
            }
        },
        'function_file_map': {name.lower(): FILE_PATH},
    }
    return meta


def call_params(function_name, current_index=0, named=None):
    params = [(named, '')] if named else [(None, '')]
    return types.SimpleNamespace(
        function_name=function_name,
        named_params=named is not None,
        params=params,
        current_index=current_index,
    )


@pytest.fixture(scope='module')
def cfdocs_provider():
    # the cfdocs module loads certifi, which Sublime Text provides
    certifi = types.ModuleType('certifi')
    certifi.where = lambda: None
    with mock.patch.dict(sys.modules, {'certifi': certifi}):
        from CFML.src.providers.cfdocs import cfdocs

        yield cfdocs


def test_param_header_escapes_once():
    html = minihtml.param_header({'name': 'a<b', 'type': 'R&D', 'required': True})
    assert '<strong>a&lt;b: <span class="storage-type">R&amp;D</span></strong>' in html
    assert '<span class="required">&nbsp;Required&nbsp;</span>' in html


def test_method_doc_header_shows_names_and_types_as_text():
    meta = tag_function(
        returntype='Query<Row>',
        access='R&D',
        parameters=[{'name': '<!--', 'type': 'a<b'}],
    )
    doc = documentation.build_method_documentation(meta, 'f', 'Us<er', 'f', folders=())
    assert doc.header == (
        '<span class="storage-modifier">R&amp;D</span> '
        '<span class="entity-name-class">Us&lt;er</span>.'
        '<span class="entity-name-function">f</span>(): '
        '<span class="storage-type">Query&lt;Row&gt;</span>'
    )
    assert '<strong>&lt;!--: <span class="storage-type">a&lt;b</span>' in (doc.body)


def test_method_doc_paths_are_text_in_their_links():
    meta = tag_function()
    meta['function_file_map']['f'] = '/site/R&D/<x>.cfc'
    doc = documentation.build_method_documentation(meta, 'f', None, 'f', folders=())
    assert '<a href="f">/site/R&amp;D/&lt;x&gt;.cfc</a>' in doc.body
    preview = documentation.build_method_preview_doc(
        meta, 'f', '<div>preview</div>', folders=()
    )
    assert preview.link == (
        '<strong>path</strong>: '
        '<a class="plain-link" href="f">/site/R&amp;D/&lt;x&gt;.cfc</a>'
    )
    assert preview.body == '<div>preview</div>'


def test_doc_paths_are_shown_relative_to_the_project_folder():
    meta = tag_function()
    meta['function_file_map']['f'] = '/site/model/User.cfc'
    doc = documentation.build_method_documentation(
        meta, 'f', None, 'f', folders=('/site',)
    )
    # the link is the same: only the text it shows is shorter
    assert doc.body == (
        '<div class="path"><strong>path</strong>: <a href="f">model/User.cfc</a></div>'
    )
    preview = documentation.build_method_preview_doc(
        meta, 'f', '<div>preview</div>', folders=('/site',)
    )
    assert preview.link == (
        '<strong>path</strong>: <a class="plain-link" href="f">model/User.cfc</a>'
    )

    meta = extended('component {}', file_path='/site/model/User.cfc')
    body = documentation.build_documentation(
        meta, '/site/model/User.cfc', 'User', folders=('/site',)
    ).body
    assert '<a href="__go_to_component">model/User.cfc</a>' in body

    # with several folders, after the name of the one the file is in
    body = documentation.build_documentation(
        meta, '/site/model/User.cfc', 'User', folders=('/lib', '/site')
    ).body
    assert '<a href="__go_to_component">site/model/User.cfc</a>' in body

    # a file outside every folder is shown whole
    body = documentation.build_documentation(
        meta, '/other/User.cfc', 'User', folders=('/site',)
    ).body
    assert '<a href="__go_to_component">/other/User.cfc</a>' in body


def test_relative_doc_paths_are_text_in_their_links():
    meta = tag_function()
    meta['function_file_map']['f'] = '/R&D/<x>/a&b/User.cfc'
    folders = ('/R&D/<x>', '/site')
    doc = documentation.build_method_documentation(
        meta, 'f', None, 'f', folders=folders
    )
    assert '<a href="f">&lt;x&gt;/a&amp;b/User.cfc</a>' in doc.body
    preview = documentation.build_method_preview_doc(meta, 'f', '', folders=folders)
    assert preview.link.endswith('href="f">&lt;x&gt;/a&amp;b/User.cfc</a>')


def test_function_call_params_show_names_and_types_as_text():
    meta = tag_function(
        parameters=[
            {'name': 'a<b', 'type': 'R&D', 'required': True},
            {'name': 'c&d'},
            {'name': '{a, b: {c}}', 'destructuring': True},
        ]
    )
    doc = documentation.build_function_call_params_doc(
        meta, call_params('f'), None, 'f'
    )
    assert doc.arguments == (
        '(<span class="argument-active">a&lt;b</span>, '
        '<span class="argument-optional">c&amp;d</span>, '
        '<span class="argument-optional">{a, b: {c}}</span>)'
    )
    assert doc.body.startswith(
        '<em>Type:</em> <span class="signature">'
        '<span class="storage-type">R&amp;D</span></span><br>'
    )


def test_component_doc_shows_names_paths_and_properties_as_text():
    meta = extended(
        '<cfcomponent extends="a&b" entityname="<e">\n'
        '<cfproperty name="p&q" type="R&D" inject="id:x<y">\n'
        '</cfcomponent>',
        file_path='/site/R&D/User.cfc',
    )
    meta['property_file_map']['p&q'] = '/site/R&D/<Base>.cfc'
    doc = documentation.build_documentation(
        meta, '/site/R&D/User.cfc', 'R&D.User', folders=()
    )
    assert doc.header == '<span class="entity-name-class">R&amp;D.User</span>'
    body = doc.body
    assert '<a href="__go_to_component">/site/R&amp;D/User.cfc</a>' in body
    assert (
        '<strong>entityname: <span class="string-quoted">&lt;e</span></strong>' in body
    )
    assert (
        '<strong>extends: <span class="entity-other-inherited-class">a&amp;b</span>'
        in body
    )
    assert (
        '<strong>p&amp;q: <span class="storage-type">R&amp;D</span></strong>'
        ' <small><em>(from &lt;Base&gt;.cfc)</em></small>'
    ) in body
    assert '<em>Inject:</em> id:x&lt;y' in body


def test_component_doc_method_cards_show_names_and_files_as_text():
    meta = tag_function(name='f', returntype='R&D')
    meta['function_file_map']['f'] = '/site/<Base>.cfc'
    meta.update(
        {
            'initmethod': None,
            'properties': {},
            'property_file_map': {},
            'accessors': False,
            'persistent': False,
        }
    )
    body = documentation.build_documentation(meta, FILE_PATH, 'User', folders=()).body
    assert (
        '<a class="plain-link" href="f"><span class="entity-name-function">f</span>(): '
        '<span class="storage-type">R&amp;D</span></a>'
    ) in body
    assert '<small><em>(from &lt;Base&gt;.cfc)</em></small>' in body


def test_ordinary_text_and_the_docs_own_markup_are_unchanged():
    meta = extended(
        'component extends="models.Base" accessors="true" {\n'
        '    property name="name" type="string";\n'
        '    public string function find(required numeric id) {}\n'
        '}'
    )
    doc = documentation.build_documentation(meta, FILE_PATH, 'models.User', folders=())
    assert doc.header == ('<span class="entity-name-class">models.User</span>')
    body = doc.body
    assert '<a href="__go_to_component">/site/model/User.cfc</a>' in body
    assert '<span class="entity-other-inherited-class">models.Base</span>' in body
    assert '<strong>accessors: <span class="constant-language">true</span>' in body
    assert '<strong>name: <span class="storage-type">string</span></strong>' in body
    assert (
        '<a class="plain-link" href="find"><span class="entity-name-function">find</span>'
        '(...): <span class="storage-type">string</span></a>'
    ) in body
    assert (
        '<strong>id: <span class="storage-type">numeric</span></strong>'
        ' <span class="required">&nbsp;Required&nbsp;</span>'
    ) in body


def test_dotpath_and_custom_tag_paths_are_text_in_their_links():
    from CFML.src.providers.custom_tags import documentation as custom_tag_docs
    from CFML.src.providers.components import dot_path_documentation as dotpath_docs

    doc, _ = dotpath_docs.get_documentation(
        None, '/site/R&D/<x>.cfc', '<span class="entity-name-class">x</span>', ()
    )
    assert doc.header == '<span class="entity-name-class">x</span>'
    assert '<a href="__go_to_component">/site/R&amp;D/&lt;x&gt;.cfc</a>' in (doc.body)

    tag_info = {'has_end_tag': False, 'attributes': ['a']}
    doc, _ = custom_tag_docs.get_documentation(
        None, 'cf_x', '/tags/R&D/x.cfm', tag_info, ()
    )
    # the path is in the body, which is what the popup shows
    assert doc.body.startswith(
        '<div class="path"><strong>path</strong>: '
        '<a href="__go_to_customtag">/tags/R&amp;D/x.cfm</a></div>'
    )
    # what is known of the tag is in cards, as it is for a component
    assert (
        '<strong>closing tag: <span class="constant-language">false</span></strong>'
    ) in doc.body
    assert (
        '<strong>attributes: <span class="entity-other-attribute-name">a</span></strong>'
    ) in doc.body

    doc, _ = custom_tag_docs.get_documentation(
        None, 'cf_x', '/tags/x.cfm', {'has_end_tag': True, 'attributes': []}, ()
    )
    assert 'attributes' not in doc.body


class RecordingWindow:
    def __init__(self):
        self.opened = []

    def open_file(self, path, flags=0):
        self.opened.append(path)


def test_dotpath_and_custom_tag_paths_are_relative_and_open_the_file():
    from CFML.src.providers.custom_tags import documentation as custom_tag_docs
    from CFML.src.providers.components import dot_path_documentation as dotpath_docs

    window = RecordingWindow()
    view = types.SimpleNamespace(window=lambda: window)
    doc, on_navigate = dotpath_docs.get_documentation(
        view, '/site/model/User.cfc', 'User', ('/site',)
    )
    assert doc.body == (
        '<div class="path"><strong>path</strong>: '
        '<a href="__go_to_component">model/User.cfc</a></div>'
    )
    on_navigate('__go_to_component')

    tag_info = {'has_end_tag': False, 'attributes': []}
    doc, on_navigate = custom_tag_docs.get_documentation(
        view, 'cf_x', '/site/tags/x.cfm', tag_info, ('/site',)
    )
    assert doc.body.startswith(
        '<div class="path"><strong>path</strong>: '
        '<a href="__go_to_customtag">tags/x.cfm</a></div>'
    )
    on_navigate('__go_to_customtag')
    # what the links open is the whole path, as before
    assert window.opened == ['/site/model/User.cfc', '/site/tags/x.cfm']


def test_cfdocs_headers_are_unchanged(cfdocs_provider):
    data = {
        'name': 'queryExecute',
        'type': 'function',
        'returns': 'query',
        'params': [
            {'name': 'sql', 'required': True},
            {'name': 'params', 'required': False},
        ],
    }
    assert cfdocs_provider.build_cfdoc_header(data) == (
        '<span class="entity-name-function">queryExecute</span>('
        '<span class="variable-parameter-function">sql</span>'
        '[, <span class="variable-parameter-function">params</span>]): '
        '<span class="storage-type">query</span>'
    )
    tag = {
        'name': 'cfquery',
        'type': 'tag',
        'params': [{'name': 'name', 'required': True}],
    }
    assert cfdocs_provider.build_cfdoc_header(tag) == (
        '&lt;<span class="entity-name-tag-cfml">cfquery</span>'
        ' <span class="entity-other-attribute-name">name</span>=""&gt;'
    )


HINTED = """/**
 * Builds a <cfquery>
 * for R&D
 */
component {
    /**
     * Runs it
     * <!-- twice
     * @sep The <br> to join with
     */
    public string function run(string sep, numeric n hint="a & b") {}

    /**
     * Finds a user
     * @id The user id
     */
    public function find(required numeric id) {}
}
"""


def test_docblock_hints_are_stored_as_text():
    meta = parse_cfc_file_string(HINTED)
    assert meta['hint'] == 'Builds a <cfquery>\nfor R&D'
    run = meta['functions']['run']['meta']
    assert run['hint'] == 'Runs it\n<!-- twice'
    assert run['parameters'][0]['hint'] == 'The <br> to join with'


def test_method_doc_shows_hints_as_text():
    meta = extended(HINTED)
    body = documentation.build_method_documentation(
        meta, 'run', None, 'run', folders=()
    ).body
    assert '<div class="card-body">Runs it<br>&lt;!-- twice</div>' in body
    assert '<div class="card-body">The &lt;br&gt; to join with</div>' in body
    assert '<div class="card-body">a &amp; b</div>' in body


def test_function_call_params_doc_shows_hints_as_text():
    meta = extended(HINTED)
    doc = documentation.build_function_call_params_doc(
        meta, call_params('run'), None, 'run'
    )
    assert doc.body.endswith('<p>The &lt;br&gt; to join with</p>')
    doc = documentation.build_function_call_params_doc(
        meta, call_params('run', named='n'), None, 'run'
    )
    assert doc.body.endswith('<p>a &amp; b</p>')


def test_component_doc_shows_hints_as_text():
    body = documentation.build_documentation(
        extended(HINTED), FILE_PATH, 'User', folders=()
    ).body
    assert (
        '<div class="card-body">Builds a &lt;cfquery&gt;<br>for R&amp;D</div>' in body
    )
    assert '<div>Runs it<br>&lt;!-- twice</div>' in body
    assert '</strong></span><br>The &lt;br&gt; to join with</li>' in body
    assert '</strong></span><br>a &amp; b</li>' in body
    # ordinary hints are unchanged
    assert '<div>Finds a user</div>' in body
    assert '<br>The user id</li>' in body


def test_tag_hints_are_text():
    meta = extended(
        '<cfcomponent hint="R&D <cfquery">\n'
        '<cffunction name="f" hint="a<b">\n'
        '    <cfargument name="x" hint="c & d">\n'
        '</cffunction>\n'
        '</cfcomponent>'
    )
    body = documentation.build_documentation(meta, FILE_PATH, 'User', folders=()).body
    assert '<div class="card-body">R&amp;D &lt;cfquery</div>' in body
    assert '<div>a&lt;b</div>' in body
    assert '<br>c &amp; d</li>' in body


DEFAULTS = """component {
    public function join(
        string sep = "<br>",
        string open = "<!--",
        string dept = "R&D",
        numeric count = 1,
        {a, b: {c}} = {}
    ) {}
}
"""


def test_method_doc_shows_defaults_as_text():
    body = documentation.build_method_documentation(
        extended(DEFAULTS), 'join', None, 'join', folders=()
    ).body
    for default in ['"&lt;br&gt;"', '"&lt;!--"', '"R&amp;D"', '1', '{}']:
        assert (
            '<p><em>Default:</em> <span class="code">' + default + '</span></p>'
        ) in body
    assert '<strong>{a, b: {c}}</strong>' in body


def test_function_call_params_doc_shows_defaults_as_text():
    meta = extended(DEFAULTS)
    bodies = [
        documentation.build_function_call_params_doc(
            meta, call_params('join', index), None, 'join'
        ).body
        for index in range(5)
    ]
    for body, default in zip(
        bodies, ['"&lt;br&gt;"', '"&lt;!--"', '"R&amp;D"', '1', '{}'], strict=True
    ):
        assert body.endswith(
            '<br><em>Default:</em> <span class="code">' + default + '</span>'
        )


def test_component_doc_shows_defaults_as_text():
    body = documentation.build_documentation(
        extended(DEFAULTS), FILE_PATH, 'User', folders=()
    ).body
    for default in ['"&lt;br&gt;"', '"&lt;!--"', '"R&amp;D"', '1']:
        assert (
            '<br><em>Default:</em> <span class="code">' + default + '</span></li>'
        ) in body
    assert '<br><em>Default:</em> <span class="code">{}</span></li></ul>' in body


def test_cfdocs_fetch_errors_are_text(cfdocs_provider, monkeypatch):
    from CFML.src import cfdocs_store

    def urlopen(url, timeout, context):
        raise urllib.error.URLError('timed out')

    monkeypatch.setattr(cfdocs_store.urllib.request, 'urlopen', urlopen)
    monkeypatch.setattr(cfdocs_store, 'cfdocs_failed_requests', collections.deque())
    data, success = cfdocs_store.request_cfdoc('cfquery')
    assert success is False
    body = cfdocs_provider.build_cfdoc_error('cfquery', data).body
    assert body == (
        'I tried to load that doc for you but got this instead:'
        '<p>Unable to fetch cfquery.json<br>&lt;urlopen error timed out&gt;</p>'
    )


def test_cfdocs_error_has_the_color_of_an_error(cfdocs_provider):
    doc = cfdocs_provider.build_cfdoc_error('cfquery', {'error_message': 'no'})
    assert doc.accent == 'redish'
    assert doc.accent != cfdocs_provider.ACCENT


def test_cfdocs_http_error_is_shown_in_paragraphs(cfdocs_provider):
    from CFML.src import cfdocs_store

    data = {'error_message': cfdocs_store.CFDOCS_HTTP_ERROR_MESSAGE}
    body = cfdocs_provider.build_cfdoc_error('cfquery', data).body
    assert body.count('<p>') == 3
    assert '<br>' not in body


def test_cfdocs_decode_errors_are_text(cfdocs_provider, monkeypatch):
    from CFML.src import cfdocs_store

    monkeypatch.setattr(
        cfdocs_store.urllib.request, 'urlopen', lambda *args, **kwargs: io.BytesIO(b'')
    )
    data, success = cfdocs_store.request_cfdoc('cfquery')
    assert success is False
    assert data['error_message'] == (
        'Unable to decode cfquery.json\n'
        'ValueError: Expecting value: line 1 column 1 (char 0)'
    )


def test_property_details_are_labeled_one_to_a_line():
    meta = extended(
        'component {\n'
        '    property name="a" type="string" getter="true" setter="true" inject="svc";\n'
        '    property name="b" type="string";\n'
        '}'
    )
    body = documentation.build_documentation(meta, FILE_PATH, 'User', folders=()).body
    assert (
        '<div class="card-body"><em>Accessors:</em> setter, getter<br>'
        '<em>Inject:</em> svc</div>'
    ) in body
    # a property with neither has a header only
    assert (
        '<div class="card-header card-header-empty">'
        '<strong>b: <span class="storage-type">string</span></strong></div>'
    ) in body
