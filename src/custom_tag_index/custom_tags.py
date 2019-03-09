import sublime
import timeit
from functools import partial
from os.path import dirname
from ..project_watcher import ProjectWatcher
from .. import utils
from . import custom_tag_index


def generate_tag_map(custom_tag_folders, index, project_file_dir):
    tag_map = {}
    for tag_folder in custom_tag_folders:
        root_path = utils.normalize_path(tag_folder["path"], project_file_dir)
        for file_path in index:
            if file_path.startswith(root_path):
                prefix = tag_folder["prefix"] + ":" if "prefix" in tag_folder else "cf_"
                tag_map[prefix + index[file_path]["tag_name"]] = file_path
    return tag_map


def generate_completions_and_closing_tags(custom_tag_folders, index, project_file_dir):
    prefixes = []
    tags = {}
    attributes = {}
    closing_tags = []

    for tag_folder in custom_tag_folders:
        root_path = utils.normalize_path(tag_folder["path"], project_file_dir)
        if "prefix" in tag_folder:
            prefixes.append(
                (
                    tag_folder["prefix"] + "\tcustom tag prefix (cfml)",
                    tag_folder["prefix"] + ":",
                )
            )
        for file_path in index:
            if file_path.startswith(root_path + "/"):
                prefix = tag_folder["prefix"] if "prefix" in tag_folder else "cf_"
                if prefix not in tags:
                    tags[prefix] = []
                key = (
                    prefix
                    + (":" if "prefix" in tag_folder else "")
                    + index[file_path]["tag_name"]
                )
                tags[prefix].append(
                    make_tag_completion(prefix, index[file_path]["tag_name"])
                )
                attributes[key] = [
                    (a + "\t" + key, a + '="$1"')
                    for a in index[file_path]["attributes"]
                ]
                if index[file_path]["has_end_tag"]:
                    closing_tags.append(key)

    return {"prefixes": prefixes, "tags": tags, "attributes": attributes}, closing_tags


def make_tag_completion(prefix, tag):
    suffix = " (" + prefix + ")" if prefix != "cf_" else ""
    comp_prefix = "cf_" if prefix == "cf_" else ""
    return (comp_prefix + tag + "\tcustom tag" + suffix, comp_prefix + tag)


class CustomTags:
    def __init__(self):
        self.folder_key = "custom_tag_folders"
        self.watcher = ProjectWatcher(self.folder_key, self.project_event_handler)
        self.data = {}
        self.listeners = []

    def project_event_handler(self, event, project_name, file_path=None):
        if event == "project_added":
            sublime.set_timeout_async(partial(self.index_project, project_name))
        elif event == "project_removed":
            self.remove_project(project_name)
        elif event == "project_updated":
            self.update_project(project_name)
        elif event == "project_file_updated":
            self.update_project_file(project_name, file_path)
        elif event == "project_file_removed":
            self.remove_project_file(project_name, file_path)

    def subscribe(self, listener):
        self.listeners.append(listener)

    def notify_listeners(self, project_name):
        for listener in self.listeners:
            listener(project_name)

    def index_project(self, project_name):
        project_data = self.watcher.projects[project_name]["project_data"]
        custom_tag_folders = project_data.get(self.folder_key, [])
        project_file_dir = dirname(project_name)

        if len(custom_tag_folders) == 0:
            return

        start_time = timeit.default_timer()
        index = {}

        print("CFML: indexing custom tags in project '" + project_name + "'")

        for tag_folder in sorted(custom_tag_folders, key=lambda d: d["path"]):
            root_path = utils.normalize_path(tag_folder["path"], project_file_dir)
            path_index = custom_tag_index.index(root_path)
            index.update(path_index)

        self.data[project_name] = {"index": index}
        self.build_project_data(project_name)

        index_time = timeit.default_timer() - start_time
        message = "CFML: indexing custom tags in project '{}' completed - {} files indexed in {:.2f} seconds"
        print(message.format(project_name, str(len(index)), index_time))
        self.notify_listeners(project_name)

    def sync_projects(self):
        self.watcher.sync_projects()

    def resync_project(self, project_name):
        self.watcher.resync_project(project_name)

    def update_project(self, project_name):
        if project_name in self.data:
            print("CFML: updating project '" + project_name + "'")
            self.build_project_data(project_name)
        self.notify_listeners(project_name)

    def remove_project(self, project_name):
        if project_name in self.data:
            del self.data[project_name]
        self.notify_listeners(project_name)

    def update_project_file(self, project_name, file_path):
        # lock for updating projects
        if project_name in self.data:
            file_index = custom_tag_index.index_file(file_path)
            with self.watcher.lock:
                if project_name in self.data:
                    self.data[project_name]["index"].update({file_path: file_index})
                    self.build_project_data(project_name)
            self.notify_listeners(project_name)

    def remove_project_file(self, project_name, file_path):
        if project_name in self.data and file_path in self.data[project_name]["index"]:
            with self.watcher.lock:
                if (
                    project_name in self.projects
                    and file_path in self.projects[project_name]["index"]
                ):
                    del self.data[project_name]["index"][file_path]
                    self.build_project_data(project_name)
            self.notify_listeners(project_name)

    def build_project_data(self, project_name):
        index = self.data[project_name]["index"]
        project_data = self.watcher.projects[project_name]["project_data"]
        custom_tag_folders = project_data.get(self.folder_key, [])
        project_file_dir = dirname(project_name)

        tags = generate_tag_map(custom_tag_folders, index, project_file_dir)
        completions, closing_tags = generate_completions_and_closing_tags(
            custom_tag_folders, index, project_file_dir
        )

        updated_data = {
            "tags": tags,
            "completions": completions,
            "closing_tags": closing_tags,
        }

        self.data[project_name].update(updated_data)

    def get_prefix_completions(self, project_name):
        completions = []
        if project_name in self.data:
            completions.extend(self.data[project_name]["completions"]["prefixes"])
            if "cf_" in self.data[project_name]["completions"]["tags"]:
                completions.extend(
                    self.data[project_name]["completions"]["tags"]["cf_"]
                )
            if len(completions) > 0:
                return completions
        return None

    def get_tag_completions(self, project_name, prefix):
        if project_name in self.data:
            if prefix in self.data[project_name]["completions"]["tags"]:
                return self.data[project_name]["completions"]["tags"][prefix]
        return None

    def get_tag_attribute_completions(self, project_name, tag_name):
        if project_name in self.data:
            if tag_name in self.data[project_name]["completions"]["attributes"]:
                return self.data[project_name]["completions"]["attributes"][tag_name]
        return None

    def get_index_by_tag_name(self, project_name, tag_name):
        if project_name in self.data:
            if tag_name in self.data[project_name]["tags"]:
                file_path = self.data[project_name]["tags"][tag_name]
                return file_path, self.data[project_name]["index"][file_path]
        return None, None

    def get_closing_custom_tags(self, project_name):
        if project_name in self.data:
            return self.data[project_name]["closing_tags"]
        return []
