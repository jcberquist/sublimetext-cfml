import itertools
import sys
import types
from unittest import mock

import pytest

view_ids = itertools.count(1)


def stand_in_modules():
    # stand-ins for the provider set, which would import every provider, and
    # for the view context, which the tests record
    cfml_providers = types.ModuleType('CFML.src.cfml_providers')
    cfml_providers.providers = []
    cfml_view = types.ModuleType('CFML.src.cfml_view')
    cfml_view.CfmlView = FakeCfmlView

    return {
        'CFML.src.cfml_providers': cfml_providers,
        'CFML.src.cfml_view': cfml_view,
    }


class FakeCfmlView:
    def __init__(self, view, position, prefix=''):
        self.view = view
        self.position = position
        self.on_data_loaded = None
        view.cfml_views.append(self)


class FakeView:
    def __init__(self):
        self.view_id = next(view_ids)
        self.popup = None
        self.shown = []
        self.updates = []
        self.cfml_views = []
        self.caret = 0

    def id(self):
        return self.view_id

    def is_valid(self):
        return True

    def sel(self):
        return [types.SimpleNamespace(begin=lambda: self.caret)]

    def is_popup_visible(self):
        return self.popup is not None

    def show_popup(self, content, **kwargs):
        self.popup = dict(kwargs, content=content)
        self.shown.append(content)

    def update_popup(self, content):
        self.updates.append(content)

    def hide_popup(self):
        popup, self.popup = self.popup, None
        if popup:
            popup['on_hide']()

    def erase_regions(self, key):
        pass

    def navigate(self, href):
        # what Sublime calls: the on_navigate given to the last show_popup
        self.popup['on_navigate'](href)


@pytest.fixture(scope='module')
def inline_documentation():
    with mock.patch.dict(sys.modules, stand_in_modules()):
        from CFML.src import inline_documentation

        yield inline_documentation


@pytest.fixture
def docs(inline_documentation, monkeypatch):
    # render a doc as its name and page so the tests can see what is shown
    def generate_documentation(view, docs, current_index, doc_type):
        doc = docs[current_index]
        return f'{doc.name} {current_index + 1}/{len(docs)}', None

    monkeypatch.setattr(
        inline_documentation, 'generate_documentation', generate_documentation
    )
    opened = []
    monkeypatch.setattr(inline_documentation.webbrowser, 'open_new_tab', opened.append)
    return types.SimpleNamespace(opened=opened)


def doc(name, on_navigate=None):
    return types.SimpleNamespace(name=name, on_navigate=on_navigate, priority=0)


def test_updated_completion_doc_paginates_the_docs_shown(inline_documentation, docs):
    view = FakeView()
    display = inline_documentation.display_documentation
    display(view, [doc('first')], 'completion_doc', 0)
    display(view, [doc('second'), doc('third')], 'completion_doc', 0)
    assert view.updates == ['second 1/2']

    view.navigate('page_1')
    assert view.updates[-1] == 'third 2/2'
    view.navigate('page_0')
    assert view.updates[-1] == 'second 1/2'


def test_updated_completion_doc_uses_the_shown_doc_handler(inline_documentation, docs):
    view = FakeView()
    hrefs = []
    display = inline_documentation.display_documentation
    display(view, [doc('cfdocs')], 'completion_doc', 0)
    display(view, [doc('method', hrefs.append)], 'completion_doc', 0)

    view.navigate('__go_to_component')
    assert hrefs == ['__go_to_component']
    assert docs.opened == []


def test_inline_doc_paginates(inline_documentation, docs):
    view = FakeView()
    hrefs = []
    display = inline_documentation.display_documentation
    display(view, [doc('first'), doc('second', hrefs.append)], 'inline_doc', 5)
    old_popup = view.popup

    view.navigate('page_1')
    assert view.popup['content'] == 'second 2/2'
    assert view.popup['location'] == 5
    # the popup replaced by the page change hides after the new one shows
    old_popup['on_hide']()
    view.navigate('__go_to_component')
    assert hrefs == ['__go_to_component']


def test_hidden_popup_clears_its_docs(inline_documentation, docs):
    view = FakeView()
    display = inline_documentation.display_documentation
    display(view, [doc('first')], 'completion_doc', 0)
    view.hide_popup()

    assert inline_documentation.view_state.get(view).doc_popup is None


def test_doc_request_in_another_view_keeps_a_refresh(
    inline_documentation, docs, monkeypatch
):
    class Provider:
        def get_inline_documentation(self, cfml_view, doc_type):
            return doc('loaded' if loaded else 'loading')

    loaded = False
    monkeypatch.setattr(inline_documentation.cfml_providers, 'providers', [Provider()])
    show = inline_documentation.show_inline_documentation
    first_view, second_view = FakeView(), FakeView()
    show(first_view, 0, 'inline_doc')
    show(second_view, 0, 'inline_doc')

    # the first view's data loads after the second view asked for a doc
    loaded = True
    first_view.cfml_views[0].on_data_loaded()
    assert first_view.shown == ['loading 1/1', 'loaded 1/1']
