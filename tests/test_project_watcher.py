import json
import types

import pytest

from CFML.src.project_watcher import Project, ProjectWatcher


class View:
    def __init__(self, file_name, text):
        self.path = file_name
        self.text = text

    def file_name(self):
        return self.path

    def size(self):
        return len(self.text)

    def substr(self, region):
        return self.text


@pytest.fixture
def watcher(monkeypatch):
    import sublime

    # the stand-in has no JSON decoding of its own
    monkeypatch.setattr(sublime, 'decode_value', json.loads, raising=False)
    watcher = ProjectWatcher()
    watcher.events = []
    watcher.subscribe(lambda *event: watcher.events.append(event))
    return watcher


def test_a_window_with_a_project_file_is_a_project(watcher, open_window):
    open_window(
        ['/site/www', '/site/lib'],
        '/site/site.sublime-project',
        {'mappings': [{'mapping': '/lib', 'path': 'lib'}]},
    )
    watcher.sync_projects()

    assert watcher.events == [('project_added', '/site/site.sublime-project')]
    assert watcher.get_project('/site/site.sublime-project') == Project(
        '/site/site.sublime-project',
        {'mappings': [{'mapping': '/lib', 'path': 'lib'}]},
        '/site',
        ('/site/lib', '/site/www'),
    )


def test_an_empty_project_file_has_no_data(watcher, open_window):
    open_window(['/site'], '/site/site.sublime-project')
    watcher.sync_projects()

    assert watcher.get_project_data('/site/site.sublime-project') == {}


def test_a_closed_window_removes_its_project(watcher, open_window, windows):
    window = open_window(['/site'], '/site/site.sublime-project', {})
    watcher.sync_projects()
    watcher.sync_projects(window)

    assert watcher.events[-1] == ('project_removed', '/site/site.sublime-project')
    assert watcher.get_project('/site/site.sublime-project') is None


def test_a_saved_project_is_updated_once(watcher, open_window):
    window = open_window(['/site'], '/site/site.sublime-project', {})
    watcher.sync_projects()

    window.data = {'cfc_folders': [{'path': 'model'}]}
    watcher.on_post_save_project_async(window)
    watcher.on_post_save_project_async(window)

    assert watcher.events[1:] == [('project_updated', '/site/site.sublime-project')]
    assert watcher.get_project_data('/site/site.sublime-project') == window.data


def test_a_project_file_saved_in_a_view_keeps_the_folders(watcher, open_window):
    open_window(['/site'], '/site/site.sublime-project', {})
    watcher.sync_projects()

    view = View('/site/site.sublime-project', '{"mappings": []}')
    watcher.on_post_save_async(view)

    assert watcher.events[1:] == [('project_updated', '/site/site.sublime-project')]
    assert watcher.get_project('/site/site.sublime-project') == Project(
        '/site/site.sublime-project', {'mappings': []}, '/site', ('/site',)
    )


def test_a_window_with_folders_and_no_project_file_is_a_project(watcher, open_window):
    # Sublime Text gives such a window project data that lists its folders
    open_window(['/site/www/', '\\site\\lib'], None, {'folders': [{'path': 'www'}]})
    watcher.sync_projects()

    name = 'folders:/site/lib|/site/www'
    assert watcher.events == [('project_added', name)]
    assert watcher.get_project(name) == Project(
        name, {}, None, ('/site/lib', '/site/www')
    )


def test_a_window_without_folders_or_a_project_file_is_not_a_project(
    watcher, open_window
):
    open_window()
    watcher.sync_projects()

    assert watcher.projects == {}


def test_two_windows_on_one_folder_share_a_project(watcher, open_window, windows):
    first = open_window(['/site'])
    second = open_window(['/site'])
    watcher.sync_projects()
    assert list(watcher.projects) == ['folders:/site']

    watcher.sync_projects(first)
    windows.remove(first)
    assert watcher.events == [('project_added', 'folders:/site')]

    watcher.sync_projects(second)
    windows.remove(second)
    assert watcher.events[1:] == [('project_removed', 'folders:/site')]
    assert watcher.projects == {}


def test_a_view_is_in_the_project_of_its_window(open_window):
    from CFML.src import utils

    window = open_window(['/site'])
    view = types.SimpleNamespace(window=lambda: window)
    assert utils.get_project_name(view) == 'folders:/site'

    no_window = types.SimpleNamespace(window=lambda: None)
    assert utils.get_project_name(no_window) is None


def test_project_settings_are_only_read_from_a_project_file(open_window, monkeypatch):
    from CFML.src import utils

    monkeypatch.setattr(utils, 'get_setting', lambda key: 'package')
    data = {'cfml_setting': 'project'}
    with_file = open_window(['/site'], '/site/site.sublime-project', data)
    without_file = open_window(['/site'], None, data)

    assert utils.get_project_setting(with_file, 'cfml_setting') == 'project'
    assert utils.get_project_setting(without_file, 'cfml_setting') == 'package'


def test_the_index_command_indexes_a_window_without_a_project_file(
    watcher, open_window, monkeypatch
):
    from CFML.src.component_index import commands

    monkeypatch.setattr(commands, 'project_watcher', watcher)
    window = open_window(['/site'])
    watcher.sync_projects()

    commands.CfmlIndexProjectCommand(window).run()

    # dropped without a removal, so the indexes keep their data meanwhile
    assert watcher.events == [
        ('project_added', 'folders:/site'),
        ('project_added', 'folders:/site'),
    ]


def test_no_index_has_data_for_a_project_without_a_project_file(
    open_window, component_index, custom_tags, monkeypatch
):
    from CFML.src.project_watcher import get_window_project, project_watcher

    window = open_window(['/site'])
    project = get_window_project(window)
    assert project is not None
    monkeypatch.setitem(project_watcher.projects, project.name, project)

    for index in [component_index, custom_tags]:
        index.project_event_handler('project_added', project.name)
        assert project.name not in index.data


def activate(window):
    return types.SimpleNamespace(window=lambda: window)


@pytest.fixture
def listener(watcher, monkeypatch):
    from CFML.src import project_watcher

    monkeypatch.setattr(project_watcher, 'project_watcher', watcher)
    return project_watcher.ProjectEventListener()


def test_a_folder_added_to_a_window_replaces_its_project(
    watcher, listener, open_window
):
    window = open_window(['/site'])
    watcher.sync_projects()

    window.folder_list.append('/lib')
    listener.on_activated_async(activate(window))

    assert sorted(watcher.events[1:]) == [
        ('project_added', 'folders:/lib|/site'),
        ('project_removed', 'folders:/site'),
    ]
    assert list(watcher.projects) == ['folders:/lib|/site']


def test_a_window_whose_folders_are_removed_has_no_project(
    watcher, listener, open_window
):
    window = open_window(['/site'])
    watcher.sync_projects()

    window.folder_list.clear()
    listener.on_post_window_command(window, 'close_folder_list', {})

    assert watcher.events[1:] == [('project_removed', 'folders:/site')]
    assert watcher.projects == {}


def test_an_activation_with_nothing_changed_does_not_sync(
    watcher, listener, open_window, monkeypatch
):
    window = open_window(['/site'])
    watcher.sync_projects()

    monkeypatch.setattr(watcher, 'sync_projects', lambda *args: pytest.fail())
    listener.on_activated_async(activate(window))
    listener.on_post_window_command(window, 'remove_folder', {'dirs': []})


def test_a_new_window_is_synced(watcher, listener, open_window):
    watcher.sync_projects()

    window = open_window(['/site'])
    listener.on_new_window_async(window)

    assert watcher.events == [('project_added', 'folders:/site')]


def test_a_window_seen_without_a_project_is_synced_once(
    watcher, listener, open_window, monkeypatch
):
    window = open_window()
    listener.on_activated_async(activate(window))

    monkeypatch.setattr(watcher, 'sync_projects', lambda *args: pytest.fail())
    listener.on_activated_async(activate(window))
    assert watcher.projects == {}


def test_a_closed_window_is_forgotten(watcher, listener, open_window, windows):
    window = open_window(['/site'])
    watcher.sync_projects()

    listener.on_pre_close_window(window)
    windows.remove(window)

    assert watcher.events[1:] == [('project_removed', 'folders:/site')]
    assert watcher.window_states == {}


def test_a_project_file_keeps_its_project_when_its_folders_change(
    watcher, listener, open_window
):
    name = '/site/site.sublime-project'
    window = open_window(['/site/www'], name, {'folders': [{'path': 'www'}]})
    watcher.sync_projects()

    window.folder_list.append('/site/lib')
    window.data = {'folders': [{'path': 'www'}, {'path': 'lib'}]}
    listener.on_activated_async(activate(window))
    # the save of the project file that Sublime Text may also report
    listener.on_post_save_project_async(window)

    assert watcher.events[1:] == [('project_updated', name)]
    assert watcher.get_project(name) == Project(
        name, window.data, '/site', ('/site/lib', '/site/www')
    )
