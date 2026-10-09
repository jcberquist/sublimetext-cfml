import types

from CFML.src import view_state


class View:
    def __init__(self):
        self.calls = []

    def id(self):
        return id(self)

    def hide_popup(self):
        self.calls.append('hide_popup')

    def erase_phantoms(self, key):
        self.calls.append(('erase_phantoms', key))

    def erase_regions(self, key):
        self.calls.append(('erase_regions', key))


def test_unloading_closes_what_the_views_show(monkeypatch):
    popup, preview, neither = View(), View(), View()
    view_state.get(popup).doc_popup = view_state.DocPopup('id', 'inline_doc', [], 0, 0)
    view_state.get(preview).preview = (object(), 0)
    window = types.SimpleNamespace(
        views=lambda include_transient: [popup, preview, neither]
    )
    monkeypatch.setattr(view_state.sublime, 'windows', lambda: [window])

    view_state.close_all()
    assert popup.calls == ['hide_popup']
    assert preview.calls == [
        ('erase_phantoms', 'cfml_method_preview'),
        ('erase_regions', 'cfml_method_preview'),
    ]
    assert view_state.get(preview).preview is None
    assert neither.calls == []
