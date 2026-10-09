import sublime
import threading
import timeit
from functools import partial
from collections.abc import Hashable
from typing import Any, NamedTuple, TypedDict, cast
from . import utils
from .project_watcher import Project, ProjectData, project_watcher


class IndexData(TypedDict):
    # the index entry of each file, by path
    index: dict[str, Any]


class Scan(NamedTuple):
    """What scan() found for a project."""

    # the index entry of each file, by path
    index: dict[str, Any]
    # what the files were found from, which build_project_data() is given
    sources: Any = None


class ProjectIndex[D: IndexData]:
    """
    Indexes the files of each open project. Subclasses say which files with
    get_scope(), scan() and belongs(), which by default index the folders
    that a project lists under folder_key, and implement accepts_file(),
    index_folder(), index_file() and build_project_data(). They also say
    what the data of a project is, of which the file index is a part.

    The data of a project is replaced whole, never updated in place, so
    readers, which do not take the lock, see either the old or the new
    data of a project. Listeners are called with (project_name,
    project_data) each time the data of a project is replaced, with None
    for a project whose data was removed.
    """

    label = 'files'

    def __init__(self, folder_key):
        self.folder_key = folder_key
        self.lock = threading.Lock()
        self.data: dict[str, D] = {}
        # the scope each project was last indexed with
        self.scopes: dict[str, Hashable] = {}
        self.listeners = []
        project_watcher.subscribe(self.project_event_handler)

    def accepts_file(self, file_path):
        """
        Returns whether a file is one this index holds: the check that
        index_folder() makes when it scans a folder.
        """
        raise NotImplementedError

    def index_folder(self, root_path) -> dict[str, Any]:
        raise NotImplementedError

    def index_file(self, file_path):
        """
        Returns the index entry of a file, or None if it cannot be read or
        parsed.
        """
        raise NotImplementedError

    def build_project_data(
        self, project_name, index, previous: D | None, changed_files, sources=None
    ) -> D:
        """
        Returns the data of a project with the given file index, as a new
        dict that holds the index. previous is the data it replaces, None
        when the project is indexed from scratch, and changed_files the
        paths whose index entries were updated or removed since. sources is
        what scan() found the files from when the project is indexed from
        scratch, and None otherwise.
        """
        raise NotImplementedError

    def get_scope(self, project_name) -> Hashable | None:
        """
        Returns what the index of a project is built from, None when nothing
        is indexed. The project is indexed again when it is updated and its
        scope is not equal to the one it was last indexed with, so this is
        cheap and runs on any thread. By default, the root paths of the
        folders listed under folder_key, in the order of their paths.
        """
        folders = sorted(self.get_folders(project_name), key=lambda d: d['path'])
        root_paths = tuple(self.get_root_path(project_name, d) for d in folders)
        return root_paths or None

    def scan(self, project_name, scope) -> Scan:
        """
        Returns the index of the files of a scope. It runs on the async
        thread. By default, that of each root path in turn.
        """
        index = {}
        for root_path in scope:
            index.update(self.index_folder(root_path))
        return Scan(index)

    def belongs(self, project_name, file_path) -> bool:
        """
        Returns whether a saved file is one the index of the project holds.
        By default, one that accepts_file() takes in one of the root paths.
        """
        return self.accepts_file(file_path) and self.in_folders(project_name, file_path)

    def is_quiet_when_empty(self, scope) -> bool:
        """
        Returns whether the console says nothing of a project indexed with
        the scope when no file is found, as for a window that has no CFML.
        Then the start of the indexing is told only once there are files.
        """
        return False

    def describe_scan(self, scan: Scan) -> list[str]:
        """
        Returns what the console says about what a scan found, after the
        start of the indexing is told.
        """
        return []

    def close(self):
        """Stops the index from following the open projects."""
        project_watcher.unsubscribe(self.project_event_handler)

    def subscribe(self, listener):
        self.listeners.append(listener)

    def publish(self, project_name, project_data: D | None):
        """
        Replaces the data of a project, or removes it when it is None, and
        hands the listeners the data, which is the snapshot for them to
        derive their own from. Called with the lock held, so the listeners
        are told of each publication in order.
        """
        if project_data is None:
            self.data.pop(project_name, None)
        else:
            self.data[project_name] = project_data
        for listener in self.listeners:
            listener(project_name, project_data)

    def get_project(self, project_name) -> Project | None:
        return project_watcher.get_project(project_name)

    def get_project_data(self, project_name) -> ProjectData:
        return project_watcher.get_project_data(project_name)

    def get_base_dir(self, project_name) -> str | None:
        """
        Returns the folder that relative paths in the project's data are
        resolved against, None for a project without a project file.
        """
        project = self.get_project(project_name)
        return project.base_dir if project else None

    def describe_project(self, project_name) -> str:
        """
        Returns how the console names a project: by its project file, or
        by its folders when it has none.
        """
        project = self.get_project(project_name)
        if project is None or project.base_dir is not None or not project.folders:
            return f"project '{project_name}'"
        noun = 'folder' if len(project.folders) == 1 else 'folders'
        return noun + ' ' + ', '.join(f"'{folder}'" for folder in project.folders)

    def get_folders(self, project_name) -> list[Any]:
        return cast(list, self.get_project_data(project_name).get(self.folder_key, []))

    def get_root_path(self, project_name, folder):
        return utils.normalize_path(folder['path'], self.get_base_dir(project_name))

    def get_root_paths(self, project_name):
        return [
            self.get_root_path(project_name, folder)
            for folder in self.get_folders(project_name)
        ]

    def in_folders(self, project_name, file_path):
        # the root paths of the default scope the project was last indexed
        # with; they have no trailing slash, so /site/model-old is not in
        # /site/model
        scope = self.scopes.get(project_name)
        if not isinstance(scope, tuple):
            return False
        return any(file_path.startswith(root_path + '/') for root_path in scope)

    def project_event_handler(self, event, project_name, file_path=None):
        if event == 'project_added':
            self.reindex_project(project_name)
        elif event == 'project_removed':
            self.scopes.pop(project_name, None)
            self.remove_project(project_name)
        elif event == 'project_updated':
            # reindexing is only needed when what is indexed changed
            if self.get_scope(project_name) != self.scopes.get(project_name):
                self.reindex_project(project_name)
            else:
                self.update_project(project_name)
        elif event == 'project_file_updated':
            if self.belongs(project_name, file_path):
                self.update_project_file(project_name, file_path)
        elif event == 'project_file_removed':
            # only a file in the index is removed from it
            self.remove_project_file(project_name, file_path)

    def reindex_project(self, project_name):
        self.scopes[project_name] = self.get_scope(project_name)
        sublime.set_timeout_async(partial(self.index_project, project_name))

    def index_project(self, project_name):
        scope = self.scopes.get(project_name)

        if scope is None:
            if project_name in self.data:
                self.remove_project(project_name)
            return

        start_time = timeit.default_timer()
        where = self.describe_project(project_name)
        started = f'CFML: indexing {self.label} in {where}'
        quiet_when_empty = self.is_quiet_when_empty(scope)

        if not quiet_when_empty:
            print(started)

        scan = self.scan(project_name, scope)
        quiet = quiet_when_empty and not scan.index
        if quiet_when_empty and not quiet:
            print(started)
        for message in self.describe_scan(scan):
            print(message)

        with self.lock:
            # the project may have closed while it was being indexed
            if project_name not in project_watcher.projects:
                return
            self.publish(
                project_name,
                self.build_project_data(
                    project_name, scan.index, None, (), scan.sources
                ),
            )

        if quiet:
            return
        index_time = timeit.default_timer() - start_time
        print(
            f'CFML: indexing {self.label} in {where} completed - '
            f'{len(scan.index)} files indexed in {index_time:.2f} seconds'
        )

    def update_project(self, project_name):
        with self.lock:
            previous = self.data.get(project_name)
            if previous is None:
                # listeners also derive data from the project's settings
                self.publish(project_name, None)
                return
            if previous['index'] or not self.is_quiet_when_empty(
                self.scopes.get(project_name)
            ):
                print('CFML: updating ' + self.describe_project(project_name))
            self.publish(
                project_name,
                self.build_project_data(project_name, previous['index'], previous, ()),
            )

    def remove_project(self, project_name):
        with self.lock:
            self.publish(project_name, None)

    def update_project_file(self, project_name, file_path):
        if project_name not in self.data:
            return
        file_index = self.index_file(file_path)
        with self.lock:
            previous = self.data.get(project_name)
            if previous is None:
                return
            index = dict(previous['index'])
            # a file that cannot be read or parsed is left out of the index,
            # as it is when a folder is scanned
            if file_index is not None:
                index[file_path] = file_index
            elif index.pop(file_path, None) is None:
                return
            self.publish(
                project_name,
                self.build_project_data(project_name, index, previous, (file_path,)),
            )

    def remove_project_file(self, project_name, file_path):
        with self.lock:
            previous = self.data.get(project_name)
            if previous is None or file_path not in previous['index']:
                return
            index = dict(previous['index'])
            del index[file_path]
            self.publish(
                project_name,
                self.build_project_data(project_name, index, previous, (file_path,)),
            )
