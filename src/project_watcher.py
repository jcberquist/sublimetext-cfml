import sublime
import threading
from os.path import dirname
from . import events, utils


class ProjectWatcher:
    """
    Emitted events:
        'project_added'
        'project_removed'
        'project_updated'
        'project_file_updated'
        'project_file_removed'
    """

    def __init__(self, folder_key, listener):
        self.lock = threading.Lock()
        self.projects = {}
        self.folder_key = folder_key
        self.listener = listener

        events.subscribe("on_load_async", lambda view: self.sync_projects())
        events.subscribe("on_close", lambda view: self.sync_projects())
        events.subscribe("on_post_save_async", self.on_post_save_async)
        events.subscribe("on_post_window_command", self.on_post_window_command)

    def sync_projects(self):
        project_list = utils.get_project_list()

        with self.lock:
            current_project_names = set(self.projects.keys())
            updated_project_names = {n for n, d in project_list}
            # print(current_project_names,updated_project_names)
            new_project_names = list(
                updated_project_names.difference(current_project_names)
            )
            stale_project_names = list(
                current_project_names.difference(updated_project_names)
            )
            # print(new_project_names,stale_project_names)

            # remove stale projects
            for project_name in stale_project_names:
                del self.projects[project_name]
                self.listener("project_removed", project_name)

            # add new projects
            for project_name, project_data in project_list:
                if project_name in new_project_names:
                    self.add_project(project_name, project_data)
                    self.listener("project_added", project_name)

    def on_post_save_async(self, view):
        file_name = utils.normalize_path(view.file_name())

        # check to see if the updated file was a .sublime-project
        if file_name.lower().endswith(".sublime-project"):
            project_name = file_name
            project_data = sublime.decode_value(
                view.substr(sublime.Region(0, view.size()))
            )
            self.project_updated(project_name, project_data)
        else:
            project_name = utils.get_project_name(view)
            if project_name:
                self.project_file_changed(
                    project_name, file_name, "project_file_updated"
                )

    def on_post_window_command(self, window, command, args):
        if command == "delete_file":

            for file_path in args["files"]:
                file_name = utils.normalize_path(file_path)
                if (
                    file_name.lower().endswith(".sublime-project")
                    and file_name in self.projects
                ):
                    self.sync_projects()
                else:
                    project_name = utils.get_project_name_from_window(window)
                    if project_name and project_name in self.projects:
                        self.project_file_changed(
                            project_name, file_name, "project_file_removed"
                        )

    def project_updated(self, project_name, updated_project_data):
        if project_name not in self.projects:
            self.sync_projects()
            return

        # if this project has already been indexed, reindexing should only be
        # necessary if the folder paths have changed
        current_paths = self.projects[project_name]["folders"]
        new_paths = self.normalize_folders(project_name, updated_project_data)

        if set(new_paths) != set(current_paths):
            with self.lock:
                if project_name in self.projects:
                    del self.projects[project_name]
            self.sync_projects()
        else:
            # project file has been updated (saved), but no folder paths were changed
            # so update project_data
            self.add_project(project_name, updated_project_data)
            self.listener("project_updated", project_name)

    def project_file_changed(self, project_name, file_path, event):
        for root_path in self.projects[project_name]["folders"]:
            if file_path.startswith(root_path):
                self.listener(event, project_name, file_path)
                break

    def resync_project(self, project_name):
        if project_name in self.projects:
            with self.lock:
                if project_name in self.projects:
                    del self.projects[project_name]
        self.sync_projects()

    def add_project(self, project_name, project_data):
        folders = self.normalize_folders(project_name, project_data)
        self.projects[project_name] = {"project_data": project_data, "folders": folders}

    def normalize_folders(self, project_name, project_data):
        project_file_dir = dirname(project_name)
        folders = []
        for folder in project_data.get(self.folder_key, []):
            folders.append(utils.normalize_path(folder["path"], project_file_dir))
        return folders
