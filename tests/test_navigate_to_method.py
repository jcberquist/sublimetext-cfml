import types

import pytest

from CFML.src.component_index import documentation, navigate_to_method
from CFML.src.providers.current_file import (
    documentation as current_file_documentation,
)

ENCODED_POSITION, FORCE_GROUP = 1, 2
HANDLERS = [documentation.on_navigate, current_file_documentation.on_navigate]


@pytest.fixture(autouse=True)
def new_file_flags(monkeypatch):
    # flags of their own, so the tests see which are passed
    monkeypatch.setattr(
        navigate_to_method.sublime,
        'NewFileFlags',
        types.SimpleNamespace(
            ENCODED_POSITION=ENCODED_POSITION, FORCE_GROUP=FORCE_GROUP
        ),
    )


class FakeWindow:
    def __init__(self, symbol_path):
        self.symbol_path = symbol_path
        self.commands = []
        self.opened = []

    def symbol_locations(self, symbol, source, type):
        # Sublime gives the native path of a file in its symbol index
        path = self.symbol_path
        return [
            types.SimpleNamespace(
                path=path, path_encoded_position=lambda: f'{path}:12:5'
            )
        ]

    def run_command(self, name, args):
        self.commands.append((name, args))

    def open_file(self, path, flags=0):
        self.opened.append((path, flags))


class FakeView:
    def __init__(self, window):
        self._window = window

    def window(self):
        return self._window

    def hide_popup(self):
        pass


@pytest.mark.parametrize('handler', [0, 1], ids=['component', 'current_file'])
@pytest.mark.parametrize(
    'file_path, symbol_path',
    [
        ('C:/site/User.cfc', 'C:\\site\\User.cfc'),
        ('/site/User.cfc', '/site/User.cfc'),
    ],
    ids=['windows', 'posix'],
)
def test_method_link_goes_to_the_method(handler, file_path, symbol_path):
    window = FakeWindow(symbol_path)
    on_navigate = HANDLERS[handler]
    on_navigate(FakeView(window), file_path, {'save': file_path}, 'save')

    [(name, args)] = window.commands
    assert name == 'cfml_navigate_to_method'
    navigate_to_method.CfmlNavigateToMethodCommand(window).run(**args)
    assert window.opened == [(f'{symbol_path}:12:5', ENCODED_POSITION | FORCE_GROUP)]


@pytest.mark.parametrize('handler', [0, 1], ids=['component', 'current_file'])
def test_component_link_opens_the_file(handler):
    window = FakeWindow('C:\\site\\User.cfc')
    on_navigate = HANDLERS[handler]
    on_navigate(FakeView(window), 'C:/site/User.cfc', {}, '__go_to_component')
    assert window.opened == [('C:/site/User.cfc', 0)]
