import types

import pytest

from CFML.src import buffer_metadata

from scope_selectors import matches
from test_component_index import BASE, CHILD, index_site, write

# the fixture below replaces it, so that a view's text is parsed as is
minimal_file_string = buffer_metadata.get_minimal_file_string


class Window:
    def __init__(self, project_name):
        self.project_name = project_name

    def project_file_name(self):
        return self.project_name

    def folders(self):
        return []


class View:
    """a view of a buffer, whose text is parsed as is"""

    def __init__(self, file_name, project_name, text, primary=None):
        self.file = file_name
        self.project_name = project_name
        self.text = text
        self.primary = primary or self
        self.changes = 0

    def id(self):
        return id(self)

    def buffer(self):
        return types.SimpleNamespace(primary_view=lambda: self.primary)

    def is_valid(self):
        return True

    def change_count(self):
        return self.primary.changes

    def file_name(self):
        return self.file

    def window(self):
        return Window(self.project_name)

    def edit(self, text):
        self.text = text
        self.changes += 1


@pytest.fixture(autouse=True)
def buffers(monkeypatch, component_index):
    monkeypatch.setattr(buffer_metadata, 'component_index', component_index)
    monkeypatch.setattr(buffer_metadata, 'get_minimal_file_string', lambda v: v.text)


@pytest.fixture
def scheduled(monkeypatch):
    """the parses that are waiting for the edits to pause"""
    callbacks = []
    monkeypatch.setattr(
        buffer_metadata.sublime,
        'set_timeout_async',
        lambda callback, delay=0: callbacks.append(callback),
    )
    return callbacks


def own_functions(view):
    listener = buffer_metadata.sublime_plugin.find_view_event_listener(
        view, buffer_metadata.BufferMetadata
    )
    return listener, list(listener.get()['functions'])


def function_files(metadata):
    return {
        name: file_path.rsplit('/', 1)[1]
        for name, file_path in metadata['function_file_map'].items()
    }


def test_an_open_buffer_sees_a_saved_parent(tmp_path, project, component_index):
    project_name, child = index_site(tmp_path, project, component_index)
    view = View(child, project_name, CHILD)
    metadata = buffer_metadata.get_cached_view_metadata(view)
    assert function_files(metadata) == {'inherited': 'Base.cfc', 'own': 'Child.cfc'}
    assert metadata['extends'] == 'model.Base'

    base = write(tmp_path / 'model' / 'Base.cfc', BASE.replace('inherited', 'renamed'))
    component_index.project_event_handler('project_file_updated', project_name, base)
    metadata = buffer_metadata.get_cached_view_metadata(view)
    assert function_files(metadata) == {'renamed': 'Base.cfc', 'own': 'Child.cfc'}


def test_a_buffer_parsed_before_its_project_is_indexed(
    tmp_path, project, component_index
):
    child = (tmp_path / 'model' / 'Child.cfc').as_posix()
    project_name = (tmp_path / 'site.sublime-project').as_posix()
    view = View(child, project_name, CHILD)
    metadata = buffer_metadata.get_cached_view_metadata(view)
    assert function_files(metadata) == {'own': 'Child.cfc'}

    index_site(tmp_path, project, component_index)
    metadata = buffer_metadata.get_cached_view_metadata(view)
    assert function_files(metadata) == {'inherited': 'Base.cfc', 'own': 'Child.cfc'}


def test_each_view_of_a_buffer_resolves_against_its_own_project(
    tmp_path, project, component_index
):
    project_name, child = index_site(tmp_path, project, component_index)
    view = View(child, project_name, CHILD)
    buffer_metadata.get_cached_view_metadata(view)

    # the same buffer, in a window without the project
    clone = View(child, None, CHILD, primary=view)
    metadata = buffer_metadata.get_cached_view_metadata(clone)
    assert function_files(metadata) == {'own': 'Child.cfc'}


def test_an_edit_is_parsed_once_the_edits_pause(scheduled):
    view = View(None, None, 'component { function one() {} }')
    listener, functions = own_functions(view)
    assert functions == ['one']

    view.edit('component { function one() {} function two() {} }')
    listener.on_modified()
    view.edit('component { function one() {} function three() {} }')
    listener.on_modified()
    # the metadata from before the edits is used until then
    assert own_functions(view)[1] == ['one']

    # the first edit was followed by another, so only the last is parsed
    scheduled[0]()
    assert own_functions(view)[1] == ['one']
    scheduled[1]()
    assert own_functions(view)[1] == ['one', 'three']


def test_a_change_that_no_parse_is_scheduled_for_is_parsed_when_read():
    view = View(None, None, 'component { function one() {} }')
    assert own_functions(view)[1] == ['one']

    # changed without an on_modified, as by a reload of the file
    view.edit('component { function two() {} }')
    assert own_functions(view)[1] == ['two']


class ScriptView:
    """a view of a .cfs file, of the given text in scopes"""

    def __init__(self, *tokens):
        self.tokens = tokens

    def find_by_selector(self, selector):
        # the regions are the indexes of the tokens, in the order of the file
        return [
            i for i, (scope, text) in enumerate(self.tokens) if matches(scope, selector)
        ]

    def substr(self, region):
        return self.tokens[region][1]


DOC = 'source.cfml.script comment.block.documentation.cfml'
DECLARATION = 'source.cfml.script meta.function.cfml meta.function.declaration.cfml'
BODY = 'source.cfml.script meta.function.cfml meta.function.body.cfml'


def parse_script(*tokens, file_name='run.cfs'):
    text = minimal_file_string(ScriptView(*tokens))
    view = View('/site/scripts/' + file_name, None, text)
    return buffer_metadata.get_cached_view_metadata(view)


def hints(metadata):
    return {
        name: function['meta'].get('hint')
        for name, function in metadata['functions'].items()
    }


def test_a_cfs_file_has_its_functions_and_no_component():
    metadata = parse_script(
        (DOC, '/**\n * Says hello.\n */'),
        (DECLARATION, 'function hello(required string name) '),
        (BODY, '{ return "hello " & name; }'),
    )
    assert hints(metadata) == {'hello': 'Says hello.'}
    assert metadata['functions']['hello']['meta']['parameters'][0]['name'] == 'name'
    assert metadata['extends'] is None


def test_each_doc_comment_of_a_cfs_file_goes_with_its_function():
    metadata = parse_script(
        (DOC, '/**\n * One.\n */'),
        (DECLARATION, 'function one() '),
        (BODY, '{'),
        (BODY + ' ' + DOC, '/**\n * Not a function.\n */'),
        (BODY, '}'),
        (DECLARATION, 'function two() '),
        (BODY, '{ }'),
        (DOC, '/**\n * Three.\n */'),
        (DECLARATION, 'function three() '),
        (BODY, '{ }'),
    )
    assert hints(metadata) == {'one': 'One.', 'two': None, 'three': 'Three.'}
