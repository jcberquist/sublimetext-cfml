import sublime, time
from functools import partial
from ..project_index import ProjectIndex
from .. import utils
from . import cfc_index, completions

__all__ = ["get_completions_by_dot_path", "get_completions_by_file_path",
"get_dot_paths", "get_extended_metadata_by_file_path",
"get_file_path_by_dot_path", "get_file_paths", "get_metadata_by_dot_path",
"get_metadata_by_file_path", "get_project_data", "component_index"]

class ComponentProjectIndex(ProjectIndex):


	def __init__(self):
		super().__init__("cfc_folders", {"index": {}, "dot_paths": {}, "completions": {}})


	def new_project(self, project_name, project_data):
		sublime.set_timeout_async(partial(self.index_project, project_name, project_data))


	def index_project(self, project_name, project_data):
		cfc_folders = project_data.get("cfc_folders", [])
		mappings = project_data.get("mappings", [])
		if len(cfc_folders) == 0:
			return

		start_time = time.clock()
		file_count = 0
		index = {}
		dot_path_map = {}
		print("CFML: indexing components in project '" + project_name + "'" )

		for cfc_folder in sorted(cfc_folders, key = lambda d: d["path"]):
			root_path = utils.normalize_path(cfc_folder["path"])
			path_index = cfc_index.index(root_path)
			index.update(path_index)

		dot_path_map = build_dot_paths(index, mappings)
		self.projects[project_name] = {"project_data": project_data, "data": {"index": index, "dot_paths": dot_path_map, "completions": {}}}
		self.projects[project_name]["data"]["completions"] = completions.build(project_name, index.keys(), get_extended_metadata_by_file_path)

		print("CFML: indexing components in project '" + project_name + "' completed - " + str(len(index)) + " files indexed in " + "{0:.2f}".format(time.clock() - start_time) + " seconds")
		self.notify_listeners(project_name)


	def update_project(self, project_name, updated_project_data):
		with self.lock:
			if project_name in self.projects:
				print("CFML: updating project '" + project_name + "'" )
				self.projects[project_name]["project_data"] = updated_project_data
				mappings = updated_project_data.get("mappings", [])
				dot_path_map = build_dot_paths(self.projects[project_name]["data"]["index"], mappings)
				self.projects[project_name]["data"]["dot_paths"] = dot_path_map
				self.projects[project_name]["data"]["completions"] = completions.build(project_name, get_file_paths(project_name), get_extended_metadata_by_file_path)
		self.notify_listeners(project_name)


	def update_project_file(self, project_name, file_path):
		file_index = cfc_index.index_file(file_path)
		# lock for updating projects
		if project_name in self.projects:
			with self.lock:
				if project_name in self.projects:
					self.projects[project_name]["data"]["index"].update({file_path: file_index})
					dot_path_map = build_dot_paths(self.projects[project_name]["data"]["index"], get_project_data(project_name).get("mappings", []))
					self.projects[project_name]["data"]["dot_paths"] = dot_path_map
					self.projects[project_name]["data"]["completions"] = completions.build(project_name, get_file_paths(project_name), get_extended_metadata_by_file_path)
			self.notify_listeners(project_name)


	def remove_project_file(self, project_name, file_path):
		if project_name in self.projects and file_path in self.projects[project_name]["data"]["index"]:
			with self.lock:
				if project_name in self.projects and file_path in self.projects[project_name]["data"]["index"]:
					del self.projects[project_name]["data"]["index"][file_path]
					project_index = self.projects[project_name]["data"]["index"]
					project_data = self.projects[project_name]["data"]["project_data"]
					dot_path_map = build_dot_paths(project_index, project_data.get("mappings", []))
					self.projects[project_name]["data"]["dot_paths"] = dot_path_map
					self.projects[project_name]["data"]["completions"] = completions.build(project_name, get_file_paths(project_name), get_extended_metadata_by_file_path)
			self.notify_listeners(project_name)


	def project_deleted(self, project_name):
		self.notify_listeners(project_name)


##############

def build_dot_paths(path_index, mappings):
	dot_paths = {}
	for file_path in path_index:
		for mapping in mappings:
			normalized_mapping = utils.normalize_mapping(mapping)
			if file_path.startswith(normalized_mapping["path"]):
				mapped_path = normalized_mapping["mapping"] + file_path.replace(normalized_mapping["path"], "")
				path_parts = mapped_path.split("/")[1:]
				dot_path = ".".join(path_parts)[:-4]
				dot_paths[dot_path.lower()] = {"file_path": file_path, "dot_path": dot_path}
	return dot_paths

def resolve_path(project_name, file_path, extends):
	dot_path = get_file_path_by_dot_path(project_name, extends.lower())
	if dot_path:
		return dot_path["file_path"]

	folder_mapping = get_folder_mapping(project_name, file_path)
	if folder_mapping:
		full_extends = folder_mapping + "." + extends
		dot_path = get_file_path_by_dot_path(project_name, full_extends.lower())
		if dot_path:
			return dot_path["file_path"]

	return None

def get_folder_mapping(project_name, file_path):
	mappings = get_project_data(project_name).get("mappings", [])
	normalized_file_name = utils.normalize_path(file_path)
	for mapping in mappings:
		normalized_mapping = utils.normalize_mapping(mapping)
		if not normalized_file_name.startswith(normalized_mapping["path"]):
			continue
		mapped_path = normalized_mapping["mapping"] + normalized_file_name.replace(normalized_mapping["path"], "")
		path_parts = mapped_path.split("/")[1:-1]
		dot_path = ".".join(path_parts)
		if len(dot_path) > 0:
			return dot_path
	return None

##############

component_index = ComponentProjectIndex()

def get_project_data(project_name):
	return component_index.projects.get(project_name, dict).get("project_data", dict)

def get_project_index(project_name):
	return component_index.projects.get(project_name, dict).get("data", dict).get("index", dict)

def get_file_paths(project_name):
	return get_project_index(project_name).keys()

def get_dot_paths(project_name):
	return component_index.projects.get(project_name, dict).get("data", dict).get("dot_paths", dict)

def get_metadata_by_file_path(project_name, file_path):
	return component_index.projects.get(project_name, dict).get("data", dict).get("index", dict).get(file_path, None)

def get_extended_metadata_by_file_path(project_name, file_path):
	return get_extended_metadata(project_name, file_path, [])

def get_completions_by_file_path(project_name, file_path):
	return component_index.projects.get(project_name, dict).get("data", dict).get("completions", dict).get(file_path, None)

def get_file_path_by_dot_path(project_name, dot_path):
	return component_index.projects.get(project_name, dict).get("data", dict).get("dot_paths", dict).get(dot_path, None)

def get_metadata_by_dot_path(project_name, dot_path):
	cfc_file_path = get_file_path_by_dot_path(project_name, dot_path)
	if cfc_file_path:
		return get_metadata_by_file_path(project_name, cfc_file_path["file_path"])
	return None

def get_completions_by_dot_path(project_name, dot_path):
	cfc_file_path = get_file_path_by_dot_path(project_name, dot_path)
	if cfc_file_path:
		return get_completions_by_file_path(project_name, cfc_file_path["file_path"])
	return None

def get_extended_metadata(project_name, file_path, stack):
	"""
	returns the full metadata for a given cfc file path
	this is used, rather than just `cfc_index[file_path]["functions"]`
	in order to take into account the `extends` attribute
	"""
	base_meta = get_metadata_by_file_path(project_name, file_path)

	if not base_meta:
		return None

	extended_meta = {k: base_meta[k] for k in ["extends","initmethod","entityname","accessors","persistent"]}
	extended_meta.update({"functions": {}, "function_file_map": {}, "properties": {}, "property_file_map": {}})

	if base_meta["extends"]:
		extends_file_path = resolve_path(project_name, file_path, base_meta["extends"])
		if file_path not in stack:
			stack.append(file_path)
			root_meta = get_extended_metadata(project_name, extends_file_path, stack)
			if root_meta:
				for key in ["functions", "function_file_map", "properties", "property_file_map"]:
					extended_meta[key].update(root_meta[key])

	extended_meta["functions"].update(base_meta["functions"])
	extended_meta["function_file_map"].update({funct_key: file_path for funct_key in base_meta["functions"]})
	extended_meta["properties"].update(base_meta["properties"])
	extended_meta["property_file_map"].update({prop_key: file_path for prop_key in base_meta["properties"]})
	return extended_meta