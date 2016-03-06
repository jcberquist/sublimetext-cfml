import sublime
from .. import model_index
from .. import utils
from ..completions import CompletionList
from . import cfc_utils

projects = {}

def build_project_map(project_name):
	global projects
	data = {}
	path_completions, constructor_completions = make_completions(project_name)
	data["path_completions"] = path_completions
	data["constructor_completions"] = constructor_completions
	projects[project_name] = data

def make_completions(project_name):
	dot_paths = model_index.get_dot_paths(project_name)
	path_map = map_paths(dot_paths)
	path_completions = {}
	constructor_completions = {}
	for k in path_map:
		path_completions[k] = []
		constructor_completions[k] = []
		for c in sorted(path_map[k], key=lambda i: i["path_part"]):
			path_completions[k].append(make_completion(c, k, dot_paths, project_name, False))
			constructor_completions[k].append(make_completion(c, k, dot_paths, project_name, True))
	return path_completions, constructor_completions

def make_completion(path_part_dict, key, dot_paths, project_name, constructor):
	completion = path_part_dict["path_part"]
	if path_part_dict["is_cfc"] and constructor:
		full_key = key + ("." if len(key) > 0 else "") + completion
		constructor_completion = model_index.get_completions_by_file_path(project_name, dot_paths[full_key.lower()]["file_path"])["constructor"]
		if constructor_completion:
			completion = completion + constructor_completion.content[4:]
		else:
			completion = completion + "()"
	if not path_part_dict["is_cfc"]:
		completion += "."
	return path_part_dict["path_part"] + "\t" + ("cfc" if path_part_dict["is_cfc"] else "cfc path"), completion

def map_paths(dot_paths):
	path_map = {}
	for path_key in dot_paths:
		path_parts = dot_paths[path_key]["dot_path"].split(".")
		for i in range(len(path_parts)):
			key = ".".join(path_parts[:i]).lower()
			if key not in path_map:
				path_map[key] = []
			is_cfc = i == len(path_parts) - 1
			path_part_dict = {"path_part": path_parts[i], "is_cfc": is_cfc}
			if path_part_dict not in path_map[key]:
				path_map[key].append(path_part_dict)
	return path_map

def get_tag_attributes(view, prefix, position, info):
	if not info["project_name"] or info["project_name"] not in projects:
		return None

	if view.match_selector(position - 1, "meta.class.inheritance.cfml -entity.other.inherited-class.cfml"):
		cfc_path = ""
		folder_cfc_path = cfc_utils.get_folder_cfc_path(view, info["project_name"], cfc_path)

		completions = []
		completions.extend(get_completions(info["project_name"], cfc_path, "path_completions"))
		completions.extend(get_completions(info["project_name"], folder_cfc_path, "path_completions"))

		if len(completions) > 0:
			return CompletionList(completions, 2, True)

	if view.match_selector(position - 1, "entity.other.inherited-class.cfml"):
		r = utils.get_scope_region_containing_point(view, position - 1, "entity.other.inherited-class.cfml")
		r = sublime.Region(r.begin(), position - len(prefix))
		cfc_path = ".".join(view.substr(r).split(".")[:-1])
		folder_cfc_path = cfc_utils.get_folder_cfc_path(view, info["project_name"], cfc_path)

		completions = []
		completions.extend(get_completions(info["project_name"], cfc_path, "path_completions"))
		completions.extend(get_completions(info["project_name"], folder_cfc_path, "path_completions"))

		if len(completions) > 0:
			return CompletionList(completions, 2, True)

def get_script_completions(view, prefix, position, info):
	if not info["project_name"] or info["project_name"] not in projects:
		return None

	if view.match_selector(position, "meta.support.function-call.createcomponent.cfml string.quoted"):
		r = utils.get_scope_region_containing_point(view, position, "string.quoted")
		r = sublime.Region(r.begin(), position + 1)
		cfc_path = view.substr(r)
		if cfc_path[0] not in ["\"","'"] or cfc_path[-1] not in ["\"","'"]:
			return None
		cfc_path = ".".join(cfc_path[1:-1].split(".")[:-1])
		folder_cfc_path = cfc_utils.get_folder_cfc_path(view, info["project_name"], cfc_path)

		completions = []
		completions.extend(get_completions(info["project_name"], cfc_path, "path_completions"))
		completions.extend(get_completions(info["project_name"], folder_cfc_path, "path_completions"))

		if len(completions) > 0:
			return CompletionList(completions, 2, True)

	if view.match_selector(position - 1, "meta.instance.constructor.cfml"):
		r = utils.get_scope_region_containing_point(view, position - 1, "meta.instance.constructor.cfml")
		r = sublime.Region(r.begin(), position - len(prefix))
		cfc_path = ".".join(view.substr(r)[4:].split(".")[:-1])
		folder_cfc_path = cfc_utils.get_folder_cfc_path(view, info["project_name"], cfc_path)

		completions = []
		completions.extend(get_completions(info["project_name"], cfc_path, "constructor_completions"))
		completions.extend(get_completions(info["project_name"], folder_cfc_path, "constructor_completions"))

		if len(completions) > 0:
			return CompletionList(completions, 2, True)

	return None

def get_dot_completions(view, prefix, position, info):
	if not info["project_name"] or len(info["dot_context"]) == 0:
		return None

	pt = position - len(prefix)
	component_name = None

	if info["dot_context"][0].name == "createobject" and view.match_selector(pt - 2, "meta.support.function-call.createcomponent.cfml"):
		component_name = cfc_utils.get_component_name(view.substr(info["dot_context"][0].args_region))
	elif view.match_selector(pt - 2, "meta.instance.constructor.cfml"):
		component_name = ".".join([s.name for s in reversed(info["dot_context"])])

	if component_name:
		comp = model_index.get_completions_by_dot_path(info["project_name"], component_name.lower())

		if not comp:
			folder_cfc_path = cfc_utils.get_folder_cfc_path(view, info["project_name"], component_name)
			comp = model_index.get_completions_by_dot_path(info["project_name"], folder_cfc_path)

		if comp:
			completions = [(completion.key + "\t" + completion.file_path.split("/").pop(), completion.content) for completion in comp["functions"]]
			return CompletionList(completions, 1, True)

	return None

def get_completions(project_name, cfc_path, completion_type):
	if cfc_path is not None and cfc_path.lower() in projects[project_name][completion_type]:
		return projects[project_name][completion_type][cfc_path.lower()]
	return []
