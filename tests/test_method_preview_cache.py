import sys
import types
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).parent.parent
GLOBALS = {'background': '#ffffff', 'foreground': '#000000'}


def stand_in_modules():
    # just enough of the sublime module to import the component docs, with
    # the packages they live in standing in for the real ones, whose
    # __init__ modules load the component index and the providers
    sublime = types.ModuleType('sublime')
    sublime.PointClassification = types.SimpleNamespace(
        WORD_START=1, WORD_END=2, PUNCTUATION_START=4, PUNCTUATION_END=8
    )

    modules = {'sublime': sublime}
    for name, path in [
        ('CFML', ROOT),
        ('CFML.src', ROOT / 'src'),
        ('CFML.src.component_index', ROOT / 'src/component_index'),
    ]:
        modules[name] = types.ModuleType(name)
        modules[name].__path__ = [str(path)]
    return modules


class FakeWindow:
    def create_output_panel(self, name, unlisted=False):
        return mock.Mock()

    def destroy_output_panel(self, name):
        pass


class FakeView:
    def __init__(self, settings, style=GLOBALS):
        self._settings = settings
        self._style = style

    def settings(self):
        return self._settings

    def style(self):
        return dict(self._style)

    def window(self):
        return FakeWindow()


@pytest.fixture(scope='module')
def documentation():
    with mock.patch.dict(sys.modules, stand_in_modules()):
        from CFML.src.component_index import documentation

        yield documentation


@pytest.fixture
def previews(documentation, tmp_path):
    # the previews built, in order; each one is numbered
    built = []

    def build_method_preview(panel, function_name):
        built.append(function_name)
        return f'preview {len(built)}'

    file_path = tmp_path / 'User.cfc'
    file_path.write_text('component {}')
    cache = {}

    def preview(view):
        with mock.patch.object(
            documentation, 'build_method_preview', build_method_preview
        ):
            return documentation.cached_method_preview(
                view, cache, str(file_path), 'save'
            )

    return preview


def test_the_same_scheme_reuses_the_preview(previews):
    view = FakeView({'color_scheme': 'Mariana.sublime-color-scheme'})
    assert previews(view) == 'preview 1'
    assert previews(view) == 'preview 1'


def test_another_scheme_with_the_same_globals_rebuilds_it(previews):
    assert previews(FakeView({'color_scheme': 'One.sublime-color-scheme'})) == (
        'preview 1'
    )
    assert previews(FakeView({'color_scheme': 'Two.sublime-color-scheme'})) == (
        'preview 2'
    )


def test_auto_rebuilds_it_when_its_light_or_dark_scheme_changes(previews):
    settings = {
        'color_scheme': 'auto',
        'light_color_scheme': 'One.sublime-color-scheme',
        'dark_color_scheme': 'Mariana.sublime-color-scheme',
    }
    assert previews(FakeView(settings)) == 'preview 1'
    settings['light_color_scheme'] = 'Two.sublime-color-scheme'
    assert previews(FakeView(settings)) == 'preview 2'
    # switching between them changes the globals
    dark = {'background': '#303841', 'foreground': '#d8dee9'}
    assert previews(FakeView(settings, dark)) == 'preview 3'
