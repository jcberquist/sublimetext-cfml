import sublime
import timeit
import os
from functools import partial
from ..project_watcher import ProjectWatcher
from .. import utils
from .. import component_parser
from . import completions
from . import documentation


def build_dot_paths(path_index, mappings, project_file_dir):
    dot_paths = {}
    for file_path in path_index:
        for mapping in mappings:
            normalized_mapping = utils.normalize_mapping(mapping, project_file_dir)
            if file_path.startswith(normalized_mapping["path"]):
                mapped_path = normalized_mapping["mapping"] + file_path.replace(normalized_mapping["path"], "")
                path_parts = mapped_path.split("/")[1:]
                dot_path = ".".join(path_parts)[:-4]
                dot_paths[dot_path.lower()] = {"file_path": file_path, "dot_path": dot_path}
    return dot_paths


def build_entities(path_index):
    entities = {}
    for file_path, metadata in path_index.items():
        if not metadata["persistent"]:
            continue
        cfc_path, file_ext = os.path.splitext(file_path)
        cfc_name = cfc_path.split("/").pop()
        entity_name = metadata["entityname"] if metadata["entityname"] else cfc_name
        entities[entity_name.lower()] = {"file_path": file_path, "entity_name": entity_name}
    return entities


class ComponentIndex():

    def __init__(self):
        self.folder_key = 'cfc_folders'
        self.watcher = ProjectWatcher(self.folder_key, self.project_event_handler)
        self.parser = None
        self.data = {}
        self.listeners = []

    def init_parser(self):
        cache_dir = os.path.join(sublime.packages_path(), "User", "CFML")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        cache_path = cache_dir + '/cfc_index_cache.sqlite'
        self.parser = component_parser.Parser(cache_path)

    def project_event_handler(self, event, project_name, file_path=None):
        if event == 'project_added':
            sublime.set_timeout_async(partial(self.index_project, project_name))
        elif event == 'project_removed':
            self.remove_project(project_name)
        elif event == 'project_updated':
            self.update_project(project_name)
        elif event == 'project_file_updated':
            self.update_project_file(project_name, file_path)
        elif event == 'project_file_removed':
            self.remove_project_file(project_name, file_path)

    def subscribe(self, listener):
        self.listeners.append(listener)

    def notify_listeners(self, project_name):
        for listener in self.listeners:
            listener(project_name)

    def index_project(self, project_name):
        project_data = self.watcher.projects[project_name]["project_data"]
        cfc_folders = project_data.get(self.folder_key, [])
        mappings = project_data.get("mappings", [])
        project_file_dir = os.path.dirname(project_name)

        if len(cfc_folders) == 0:
            return

        start_time = timeit.default_timer()
        index = {}

        print("CFML: indexing components in project '" + project_name + "'")

        for cfc_folder in sorted(cfc_folders, key=lambda d: d["path"]):
            root_path = utils.normalize_path(cfc_folder["path"], project_file_dir)
            path_index = self.parser.parse_directory(root_path)
            index.update(path_index)

        self.data[project_name] = {
            "index": index,
            "cache": {file_path: {} for file_path in index}
        }
        self.build_project_data(project_name)

        index_time = timeit.default_timer() - start_time
        message = "CFML: indexing components in project '{}' completed - {} files indexed in {:.2f} seconds"
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
            file_index = self.parser.parse_file(file_path)
            with self.watcher.lock:
                if project_name in self.data:
                    self.data[project_name]["index"].update({file_path: file_index})
                    self.data[project_name]["cache"][file_path] = {}
                    self.build_project_data(project_name)
            self.notify_listeners(project_name)

    def remove_project_file(self, project_name, file_path):
        if project_name in self.data and file_path in self.data[project_name]["index"]:
            with self.watcher.lock:
                if project_name in self.projects and file_path in self.projects[project_name]["index"]:
                    del self.data[project_name]["index"][file_path]
                    del self.data[project_name]["cache"][file_path]
                    self.build_project_data(project_name)
            self.notify_listeners(project_name)

    def build_project_data(self, project_name):
        index = self.data[project_name]["index"]
        project_data = self.watcher.projects[project_name]["project_data"]
        mappings = project_data.get("mappings", [])

        updated_data = {
            "dot_paths": build_dot_paths(index, mappings, os.path.dirname(project_name)),
            "entities": build_entities(index),
            "completions": completions.build(project_name, index.keys(), self.get_extended_metadata_by_file_path)
        }

        self.data[project_name].update(updated_data)


    def get_project_data(self, project_name):
        try:
            return self.watcher.projects[project_name]["project_data"]
        except:
            return {}

    def get_project_index(self, project_name):
        try:
            return self.data[project_name]["index"]
        except:
            return {}

    def get_file_paths(self, project_name):
        try:
            return self.get_project_index(project_name).keys()
        except:
            return []

    def get_dot_paths(self, project_name):
        try:
            return self.data[project_name]["dot_paths"]
        except:
            return {}

    def get_entities(self, project_name):
        try:
            return self.data[project_name]["entities"]
        except:
            return {}

    def get_file_path_by_dot_path(self, project_name, dot_path):
        try:
            return self.data[project_name]["dot_paths"][dot_path.lower()]
        except:
            return None

    def get_file_path_by_entity_name(self, project_name, entity_name):
        try:
            return self.data[project_name]["entities"][entity_name.lower()]
        except:
            return None

    def get_cache_by_file_path(self, project_name, file_path):
        try:
            return self.data[project_name]["cache"][file_path]
        except:
            return None

    def get_metadata_by_file_path(self, project_name, file_path):
        try:
            return self.data[project_name]["index"][file_path]
        except:
            return None

    def get_extended_metadata_by_file_path(self, project_name, file_path, stack=[]):
        """
        returns the full metadata for a given cfc file path
        this is used, rather than just `cfc_index[file_path]["functions"]`
        in order to take into account the `extends` attribute
        """
        base_meta = self.get_metadata_by_file_path(project_name, file_path)

        if not base_meta:
            return None

        extended_meta = dict(base_meta)
        extended_meta.update({"functions": {}, "function_file_map": {}, "properties": {}, "property_file_map": {}})

        if base_meta["extends"]:
            extends_file_path = self.resolve_path(project_name, file_path, base_meta["extends"])
            if file_path not in stack:
                stack.append(file_path)
                root_meta = self.get_extended_metadata_by_file_path(project_name, extends_file_path, stack)
                if root_meta:
                    for key in ["functions", "function_file_map", "properties", "property_file_map"]:
                        extended_meta[key].update(root_meta[key])

        extended_meta["functions"].update(base_meta["functions"])
        extended_meta["function_file_map"].update({funct_key: file_path for funct_key in base_meta["functions"]})
        extended_meta["properties"].update(base_meta["properties"])
        extended_meta["property_file_map"].update({prop_key: file_path for prop_key in base_meta["properties"]})
        return extended_meta

    def get_metadata_by_dot_path(self, project_name, dot_path):
        cfc_file_path = self.get_file_path_by_dot_path(project_name, dot_path)
        if cfc_file_path:
            return self.get_metadata_by_file_path(project_name, cfc_file_path["file_path"])
        return None


    def get_metadata_by_entity_name(project_name, entity_name):
        cfc_file_path = self.get_file_path_by_entity_name(project_name, entity_name)
        if cfc_file_path:
            return self.get_metadata_by_file_path(project_name, cfc_file_path["file_path"])
        return None

    def get_completions_by_file_path(self, project_name, file_path):
        comp_type = utils.get_setting("cfml_cfc_completions")
        try:
            return self.data[project_name]["completions"][file_path][comp_type]
        except:
            return None

    def get_completions_by_dot_path(self, project_name, dot_path):
        cfc_file_path = self.get_file_path_by_dot_path(project_name, dot_path)
        if cfc_file_path:
            return self.get_completions_by_file_path(project_name, cfc_file_path["file_path"])
        return None

    def get_completions_by_entity_name(self, project_name, entity_name):
        cfc_file_path = self.get_file_path_by_entity_name(project_name, entity_name)
        if cfc_file_path:
            return self.get_completions_by_file_path(project_name, cfc_file_path["file_path"])
        return None

    def resolve_path(self, project_name, file_path, extends):
        dot_path = self.get_file_path_by_dot_path(project_name, extends.lower())
        if dot_path:
            return dot_path["file_path"]

        folder_mapping = self.get_folder_mapping(project_name, file_path)
        if folder_mapping:
            full_extends = folder_mapping + "." + extends
            dot_path = self.get_file_path_by_dot_path(project_name, full_extends.lower())
            if dot_path:
                return dot_path["file_path"]

        return None

    def get_folder_mapping(self, project_name, file_path):
        project_data = self.watcher.projects[project_name]["project_data"]
        mappings = project_data.get("mappings", [])
        normalized_file_path = utils.normalize_path(file_path)
        for mapping in mappings:
            normalized_mapping = utils.normalize_mapping(mapping, os.path.dirname(project_name))
            if not normalized_file_path.startswith(normalized_mapping["path"]):
                continue
            mapped_path = normalized_mapping["mapping"] + normalized_file_path.replace(normalized_mapping["path"], "")
            path_parts = mapped_path.split("/")[1:-1]
            dot_path = ".".join(path_parts)
            if len(dot_path) > 0:
                return dot_path
        return None

    def get_documentation(self, view, project_name, file_path, class_name):
        extended_metadata = self.get_extended_metadata_by_file_path(project_name, file_path)
        return documentation.get_documentation(view, extended_metadata, file_path, class_name)

    def get_method_documentation(self, view, project_name, file_path, function_name, class_name, method_name):
        extended_metadata = self.get_extended_metadata_by_file_path(project_name, file_path)
        function_file_path = extended_metadata["function_file_map"][function_name]
        method_preview = None
        if utils.get_setting('cfml_doc_method_preview'):
            method_preview = self.cached_method_preview(view, project_name, function_file_path, function_name)

        return documentation.get_method_documentation(
            view,
            extended_metadata,
            file_path,
            function_name,
            class_name,
            method_name,
            method_preview)

    def get_method_preview(self, view, project_name, file_path, function_name):
        extended_metadata = self.get_extended_metadata_by_file_path(project_name, file_path)
        function_file_path = extended_metadata["function_file_map"][function_name]
        method_preview = self.cached_method_preview(view, project_name, function_file_path, function_name)
        return documentation.get_method_preview(view, extended_metadata, file_path, function_name, method_preview)

    def get_function_call_params_doc(self, project_name, file_path, function_call_params, class_name, method_name):
        extended_metadata = self.get_extended_metadata_by_file_path(project_name, file_path)
        return documentation.get_function_call_params_doc(extended_metadata, function_call_params, class_name, method_name)

    def cached_method_preview(self, view, project_name, file_path, function_name):
        extended_metadata = self.get_extended_metadata_by_file_path(project_name, file_path)
        function_file_path = extended_metadata["function_file_map"][function_name]
        cache = self.get_cache_by_file_path(project_name, function_file_path)
        return documentation.cached_method_preview(view, cache, function_file_path, function_name)
