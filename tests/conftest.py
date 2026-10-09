import importlib
import itertools
import os
import sys
import types
from pathlib import Path
from typing import NamedTuple

import pytest

ROOT = Path(__file__).parent.parent
SRC = ROOT / 'src'

# the component parser does not use the sublime module, so it can be
# imported as a top-level package outside Sublime Text
sys.path.insert(0, str(SRC))


class _QuickPanelItem(NamedTuple):
    trigger: str
    details: str = ''
    annotation: str = ''
    kind: object = None


class _Flags:
    # stands in for the enums of flags and kinds
    def __getattr__(self, name):
        return 0


# just enough of the sublime and sublime_plugin modules to import the
# plugin's modules; async callbacks run at once
sublime = types.ModuleType('sublime')
for name in [
    'CompletionFormat',
    'FindFlags',
    'KindId',
    'NewFileFlags',
    'PointClassification',
    'PopupFlags',
    'RegionFlags',
    'SymbolSource',
    'SymbolType',
]:
    setattr(sublime, name, _Flags())
sublime.set_timeout = lambda callback, delay=0: callback()
sublime.set_timeout_async = lambda callback, delay=0: callback()
sublime.windows = lambda: []
sublime.load_settings = lambda name: {'cfml_cfc_completions': 'basic'}
sublime.CompletionItem = lambda *args, **kwargs: (args, kwargs)
sublime.QuickPanelItem = _QuickPanelItem
sublime.Region = lambda *args: args


def _load_resource(name):
    # Packages/CFML/<path> is a file of the package
    return (ROOT / name.split('/', 2)[2]).read_text(encoding='utf-8')


sublime.load_resource = _load_resource
sys.modules.setdefault('sublime', sublime)

# cfdocs gets its certificates from certifi, which Sublime Text ships
certifi = types.ModuleType('certifi')
certifi.where = lambda: None
sys.modules.setdefault('certifi', certifi)


class _WindowCommand:
    def __init__(self, window):
        self.window = window


class _ViewEventListener:
    def __init__(self, view):
        self.view = view


view_event_listeners = {}


def _find_view_event_listener(view, cls):
    # every view has a listener of every class, created when first asked for
    key = (view.id(), cls)
    if key not in view_event_listeners:
        view_event_listeners[key] = cls(view)
    return view_event_listeners[key]


sublime_plugin = types.ModuleType('sublime_plugin')
for name in [
    'ApplicationCommand',
    'EventListener',
    'TextCommand',
]:
    setattr(sublime_plugin, name, object)
sublime_plugin.ViewEventListener = _ViewEventListener
sublime_plugin.find_view_event_listener = _find_view_event_listener
sublime_plugin.WindowCommand = _WindowCommand
sys.modules.setdefault('sublime_plugin', sublime_plugin)

# the plugin's modules use relative imports, so register the package they
# are loaded from in Sublime Text: import them as CFML.src.<module>
for package_name, package_path in [('CFML', ROOT), ('CFML.src', SRC)]:
    package = types.ModuleType(package_name)
    package.__path__ = [str(package_path)]
    sys.modules.setdefault(package_name, package)


class Window:
    """A stand-in for a window, with the folders and project file it is given."""

    ids = itertools.count(1)

    def __init__(self, folders=(), project_file_name=None, project_data=None):
        self.window_id = next(Window.ids)
        self.folder_list = list(folders)
        self.project_file = project_file_name
        self.data = project_data

    def id(self):
        return self.window_id

    def folders(self):
        return list(self.folder_list)

    def project_file_name(self):
        return self.project_file

    def project_data(self):
        return self.data


@pytest.fixture
def windows(monkeypatch):
    """The open windows, which sublime.windows() returns."""
    open_windows = []
    monkeypatch.setattr(sys.modules['sublime'], 'windows', lambda: list(open_windows))
    return open_windows


@pytest.fixture
def open_window(windows):
    """
    Returns a function that opens a window with the given folders, project
    file and project data, and returns it.
    """

    def open_window(folders=(), project_file_name=None, project_data=None):
        window = Window(folders, project_file_name, project_data)
        windows.append(window)
        return window

    return open_window


@pytest.fixture(autouse=True)
def no_view_event_listeners():
    yield
    view_event_listeners.clear()


@pytest.fixture(scope='session')
def custom_tag_index():
    # the package exports an instance under the module's name
    return importlib.import_module('CFML.src.custom_tag_index.custom_tag_index')


@pytest.fixture
def project(tmp_path, monkeypatch):
    """
    Returns a function that registers a project file in tmp_path, with the
    given project data, as an open project of a window on tmp_path. The
    project is named after its file, as in Sublime Text, unless it is given
    a name.
    """
    from CFML.src.project_watcher import Project, project_watcher

    def register(project_data, name=None):
        base_dir = tmp_path.as_posix()
        project_name = name or base_dir + '/site.sublime-project'
        project = Project(project_name, project_data, base_dir, (base_dir,))
        monkeypatch.setitem(project_watcher.projects, project_name, project)
        return project_name

    return register


@pytest.fixture
def component_index(tmp_path):
    from CFML.src.component_index.index import ComponentIndex
    from CFML.src.component_parser import Parser

    index = ComponentIndex()
    index.parser = Parser(str(tmp_path / 'cache.sqlite'))
    yield index
    index.close()


@pytest.fixture
def git_environment(tmp_path, monkeypatch):
    # git reads no configuration but the repository's own, and finds no
    # repository above tmp_path
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', os.devnull)
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'xdg'))
    monkeypatch.setenv('GIT_CEILING_DIRECTORIES', str(tmp_path))


@pytest.fixture
def settings(monkeypatch):
    """The package settings, which a test can change."""
    package_settings = {
        'cfml_cfc_completions': 'basic',
        'cfml_auto_index': True,
        'cfml_index_max_files': 5000,
    }
    monkeypatch.setattr(
        sys.modules['sublime'], 'load_settings', lambda name: package_settings
    )
    return package_settings


@pytest.fixture
def index(component_index, settings, monkeypatch):
    # the component index, as the only listener of a project watcher that
    # starts with no projects
    from CFML.src.project_watcher import project_watcher

    monkeypatch.setattr(project_watcher, 'projects', {})
    monkeypatch.setattr(project_watcher, 'window_states', {})
    monkeypatch.setattr(
        project_watcher, 'listeners', [component_index.project_event_handler]
    )
    return component_index


@pytest.fixture
def custom_tags():
    from CFML.src.custom_tag_index.custom_tags import CustomTags

    index = CustomTags()
    yield index
    index.close()
