import sublime, threading, time
from os.path import splitext
from functools import partial
from .. import utils
from . import cfc_index, completions

__all__ = ["get_completions_by_dot_path", "get_completions_by_file_path",
"get_dot_paths", "get_extended_metadata_by_file_path",
"get_file_path_by_dot_path", "get_file_paths", "get_metadata_by_dot_path",
"get_metadata_by_file_path", "get_project_data", "index_project_file",
"project_deleted", "project_updated", "remove_project_file", "subscribe",
"sync_projects"]

projects = {}
listeners = []
lock = threading.Lock()

# public api
# TODO: review these function names

def get_project_data(project_name):
	return projects.get(project_name,
		dict).get("project_data",
	dict)

def get_project_index(project_name):
	return projects.get(project_name,
		dict).get("index", dict)

def get_file_paths(project_name):
	return get_project_index(project_name).keys()

def get_dot_paths(project_name):
	return projects.get(project_name, dict).get("dot_paths", dict)

def get_metadata_by_file_path(project_name, file_path):
	return projects.get(project_name, dict).get("index", dict).get(file_path, None)

def get_extended_metadata_by_file_path(project_name, file_path):
	return get_extended_metadata(project_name, file_path, [])

def get_completions_by_file_path(project_name, file_path):
	return projects.get(project_name, dict).get("completions", dict).get(file_path, None)

def get_file_path_by_dot_path(project_name, dot_path):
	return projects.get(project_name, dict).get("dot_paths", dict).get(dot_path, None)

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

# listeners will be called with the name of the updated project
def subscribe(listener):
	listeners.append(listener)

######

def get_project_name(project_file_name):
	project_file = project_file_name.replace("\\","/").split("/").pop()
	project_name, ext = splitext(project_file)
	return project_name

def notify_listeners(project_name):
	for listener in listeners:
		listener(project_name)

def sync_projects():
	global projects
	project_list = utils.get_project_list()

	with lock:
		current_project_names = set(projects.keys())
		updated_project_names = {project_name for project_name, project_data in project_list}
		#print(current_project_names,updated_project_names)
		new_project_names = list(updated_project_names.difference(current_project_names))
		stale_project_names = list(current_project_names.difference(updated_project_names))
		#print(new_project_names,stale_project_names)
		# remove stale projects
		for project_name in stale_project_names:
			del projects[project_name]
		# add new projects
		for project_name, project_data in project_list:
			if project_name in new_project_names:
				projects[project_name] = {"project_data": project_data, "index": {}, "dot_paths": {}, "completions": {}}
	# now that projects dict is up to date release lock before initing directory load
	for project_name, project_data in project_list:
		if project_name in new_project_names:
			index_project_async(project_name, project_data)

def index_project_async(project_name, project_data):
	sublime.set_timeout_async(partial(index_project, project_name, project_data))

def index_project(project_name, project_data):
	global projects
	cfc_folders = project_data.get("cfc_folders", [])
	mappings = project_data.get("mappings", [])
	if len(cfc_folders) == 0:
		return

	start_time = time.clock()
	file_count = 0
	index = {}
	dot_path_map = {}
	print("CFML: indexing project '" + project_name + "'" )

	for cfc_folder in sorted(cfc_folders, key = lambda d: d["path"]):
		root_path = utils.normalize_path(cfc_folder["path"])
		path_index = cfc_index.index(root_path)
		index.update(path_index)

	dot_path_map = build_dot_paths(index, mappings)
	projects[project_name] = {"project_data": project_data, "index": index, "dot_paths": dot_path_map, "completions": {}}
	projects[project_name]["completions"] = completions.build(project_name, get_file_paths(project_name), get_extended_metadata_by_file_path)

	print("CFML: indexing project '" + project_name + "' completed - " + str(len(index)) + " files indexed in " + "{0:.2f}".format(time.clock() - start_time) + " seconds")
	notify_listeners(project_name)

def index_project_file(project_name, file_path):
	global projects
	if project_name not in projects:
		return
	project_data = get_project_data(project_name)
	# check for tracked file path
	cfc_folders = project_data.get("cfc_folders", [])
	for cfc_folder in cfc_folders:
		root_path = utils.normalize_path(cfc_folder["path"])
		if file_path.startswith(root_path):
			break
	else:
		return

	# if we got here this is a model folder file
	file_index = cfc_index.index_file(file_path)
	# lock for updating projects
	if project_name in projects:
		with lock:
			if project_name in projects:
				projects[project_name]["index"].update({file_path: file_index})
				dot_path_map = build_dot_paths(projects[project_name]["index"], project_data.get("mappings", []))
				projects[project_name]["dot_paths"] = dot_path_map
				projects[project_name]["completions"] = completions.build(project_name, get_file_paths(project_name), get_extended_metadata_by_file_path)
		notify_listeners(project_name)

def remove_project_file(project_name, file_path):
	global projects
	if project_name in projects and file_path in projects[project_name]["index"]:
		with lock:
			if project_name in projects and file_path in projects[project_name]["index"]:
				del projects[project_name]["index"][file_path]
				project_index = projects[project_name]["index"]
				project_data = projects[project_name]["project_data"]
				dot_path_map = build_dot_paths(project_index, project_data.get("mappings", []))
				projects[project_name]["dot_paths"] = dot_path_map
				projects[project_name]["completions"] = completions.build(project_name, get_file_paths(project_name), get_extended_metadata_by_file_path)
		notify_listeners(project_name)

def project_updated(project_name, project_data):
	global projects
	if project_name not in projects:
		sync_projects()
		return

	# if this project has already been indexed, reindexing should only be
	# necessary if the model folder paths have changed
	new_paths = [utils.normalize_path(folder["path"]) for folder in project_data.get("cfc_folders", [])]
	current_paths = [utils.normalize_path(folder["path"]) for folder in get_project_data(project_name).get("cfc_folders", [])]
	if set(new_paths) != set(current_paths):
		with lock:
			if project_name in projects:
				del projects[project_name]
		sync_projects()
	else:
		# project file has been updated (saved), but no model folder paths were changed
		# so update project_data and rebuild dot_path_map and completions
		with lock:
			if project_name in projects:
				print("CFML: updating project '" + project_name + "'" )
				projects[project_name]["project_data"] = project_data
				mappings = project_data.get("mappings", [])
				dot_path_map = build_dot_paths(projects[project_name]["index"], mappings)
				projects[project_name]["dot_paths"] = dot_path_map
				projects[project_name]["completions"] = completions.build(project_name, get_file_paths(project_name), get_extended_metadata_by_file_path)
		notify_listeners(project_name)

def project_deleted(project_name):
	global projects
	if project_name in projects:
		with lock:
			if project_name in projects:
				del projects[project_name]
		notify_listeners(project_name)


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