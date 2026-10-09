import sublime
import sublime_plugin
import threading
from dataclasses import dataclass, replace
from os.path import dirname
from typing import Any, NotRequired, TypedDict, cast
from . import utils


class Mapping(TypedDict):
    # a folder, absolute or relative to the project file
    path: str
    # the path it is mapped to, such as /model
    mapping: str


class CfcFolder(TypedDict):
    path: str
    # the variable names its components are known by, such as {cfc}Service
    variable_names: NotRequired[list[str]]
    # whether those variables are offered the accessors of the components
    accessors: NotRequired[bool]


class CustomTagFolder(TypedDict):
    path: str
    # the tags are cf_ tags without one
    prefix: NotRequired[str]


class ProjectData(TypedDict, total=False):
    """
    What the indexes read from a .sublime-project file. A project can also
    set package settings in it, which utils.get_project_setting() reads.
    """

    folders: list[dict[str, Any]]
    mappings: list[Mapping]
    cfc_folders: list[CfcFolder]
    custom_tag_folders: list[CustomTagFolder]


@dataclass(frozen=True)
class Project:
    """
    An open project, which the indexes keep their data of under its name.
    The name is a key, not a path: relative paths in the data are resolved
    against base_dir.
    """

    name: str
    # the contents of the project file, {} without one
    data: ProjectData
    # the folder of the project file, None without one
    base_dir: str | None
    # the folders of the window, normalized and sorted
    folders: tuple[str, ...]


def get_window_project(window) -> Project | None:
    """Returns the project of a window, None for a window without one."""
    project_name = utils.get_project_name_from_window(window)
    if project_name is None:
        return None
    project_file_name = window.project_file_name()
    data: ProjectData = {}
    base_dir = None
    if project_file_name:
        # a project file that is empty has no data
        data = cast(ProjectData, window.project_data() or {})
        base_dir = dirname(utils.normalize_path(project_file_name))
    return Project(project_name, data, base_dir, utils.get_window_folders(window))


# the window commands that can change the folders of a window
FOLDER_COMMANDS = {
    'close_folder_list',
    'open_recent_folder',
    'prompt_add_folder',
    'prompt_open_folder',
    'remove_folder',
}


def get_window_state(window) -> tuple[str | None, list[str]]:
    """
    Returns what the project of a window is made from, as Sublime Text
    gives it, to tell cheaply whether it changed.
    """
    return window.project_file_name(), window.folders()


def get_projects(windows) -> dict[str, Project]:
    projects = {}
    for window in windows:
        project = get_window_project(window)
        # windows on the same folders share a project
        if project is not None and project.name not in projects:
            projects[project.name] = project
    return projects


class ProjectWatcher:
    """
    Tracks the open projects and their data, and tells listeners about
    changes to them. Listeners are called with one of:
        ('project_added', project_name)
        ('project_removed', project_name)
        ('project_updated', project_name)
        ('project_file_updated', project_name, file_path)
        ('project_file_removed', project_name, file_path)
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.projects: dict[str, Project] = {}
        # the state of each open window when the projects were last synced,
        # by window id
        self.window_states: dict[int, tuple[str | None, list[str]]] = {}
        self.listeners = []

    def subscribe(self, listener):
        self.listeners.append(listener)

    def unsubscribe(self, listener):
        self.listeners.remove(listener)

    def notify(self, *event):
        for listener in self.listeners:
            listener(*event)

    def get_project(self, project_name) -> Project | None:
        return self.projects.get(project_name)

    def get_project_data(self, project_name) -> ProjectData:
        project = self.projects.get(project_name)
        return project.data if project else {}

    def get_project_folders(self, project_name) -> tuple[str, ...]:
        """
        Returns the folders of the project's window, which the docs show
        paths relative to: none for a view that is not in a project.
        """
        project = self.projects.get(project_name)
        return project.folders if project else ()

    def sync_projects(self, closing_window=None):
        windows = [
            window
            for window in sublime.windows()
            if not closing_window or window.id() != closing_window.id()
        ]
        # read before the projects, so a change in between is seen as one
        window_states = {window.id(): get_window_state(window) for window in windows}
        open_projects = get_projects(windows)

        with self.lock:
            self.window_states = window_states

            for project_name in set(self.projects) - set(open_projects):
                del self.projects[project_name]
                self.notify('project_removed', project_name)

            for project_name, project in open_projects.items():
                if project_name not in self.projects:
                    self.projects[project_name] = project
                    self.notify('project_added', project_name)

    def check_window(self, window):
        """
        Syncs the projects when the project file or the folders of a window
        are not those it had when the projects were last synced. The API
        has no event for a folder added to or removed from a window, so
        this runs after the window commands that change folders and on
        each activation of a view, and when nothing changed does only the
        cheap comparison.
        """
        if self.window_states.get(window.id()) == get_window_state(window):
            return
        self.sync_projects()
        # a window with a project file keeps its project when its folders
        # change, and only the project file's save updates it otherwise
        project = get_window_project(window)
        if project is not None:
            self.project_updated(project)

    def resync_project(self, project_name):
        # dropped without a removal, so the current index stays in use
        # until the project is indexed again
        with self.lock:
            self.projects.pop(project_name, None)
        self.sync_projects()

    def on_post_save_project_async(self, window):
        project = get_window_project(window)
        if project:
            self.project_updated(project)

    def on_post_save_async(self, view):
        file_name = utils.normalize_path(view.file_name())

        # a .sublime-project edited and saved in a view, which
        # on_post_save_project_async is not called for
        if file_name.lower().endswith('.sublime-project'):
            project = self.projects.get(file_name)
            if project is None:
                self.sync_projects()
                return
            project_data = sublime.decode_value(
                view.substr(sublime.Region(0, view.size()))
            )
            self.project_updated(replace(project, data=cast(ProjectData, project_data)))
        else:
            project_name = utils.get_project_name(view)
            if project_name in self.projects:
                self.notify('project_file_updated', project_name, file_name)

    def on_post_window_command(self, window, command, args):
        if command in FOLDER_COMMANDS:
            self.check_window(window)
            return
        if command != 'delete_file':
            return

        for file_path in args['files']:
            file_name = utils.normalize_path(file_path)
            if (
                file_name.lower().endswith('.sublime-project')
                and file_name in self.projects
            ):
                self.sync_projects()
            else:
                project_name = utils.get_project_name_from_window(window)
                if project_name in self.projects:
                    self.notify('project_file_removed', project_name, file_name)

    def project_updated(self, project: Project):
        if project.name not in self.projects:
            self.sync_projects()
            return

        # both save events can report the same save
        if self.projects[project.name] == project:
            return

        self.projects[project.name] = project
        self.notify('project_updated', project.name)


project_watcher = ProjectWatcher()


class ProjectEventListener(sublime_plugin.EventListener):
    """
    Passes the events that open, close or change a project, and those that
    save or delete a file, to the project watcher. These are window events
    and events of views of any syntax, so there is no view to listen to.
    """

    def on_load_project_async(self, window):
        project_watcher.sync_projects()

    def on_new_project_async(self, window):
        project_watcher.sync_projects()

    def on_pre_close_project(self, window):
        # the closing window still has its project, so leave it out
        project_watcher.sync_projects(window)

    def on_pre_close_window(self, window):
        project_watcher.sync_projects(window)

    def on_new_window_async(self, window):
        project_watcher.check_window(window)

    def on_activated_async(self, view):
        # the net for a change of folders that no other event reports
        window = view.window()
        if window:
            project_watcher.check_window(window)

    def on_post_save_project_async(self, window):
        project_watcher.on_post_save_project_async(window)

    def on_post_save_async(self, view):
        if not view.file_name():
            print(
                'CFML: file was saved and closed - it is not possible to determine the file path.'
            )
            return
        project_watcher.on_post_save_async(view)

    def on_post_window_command(self, window, command_name, args):
        project_watcher.on_post_window_command(window, command_name, args)


def _plugin_loaded():
    project_watcher.sync_projects()
