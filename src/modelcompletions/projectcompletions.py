import sublime, threading, time
from os.path import splitext
from functools import partial
from ..completions import CompletionList
from ..inline_documentation import Documentation
from .. import utils
from .componentfinder import load_directory, load_file, get_bean_names
from .documentation import get_documentation

projects = {}
lock = threading.Lock()

def get_project_name(project_file_name):
	project_file = project_file_name.replace("\\","/").split("/").pop()
	project_name, ext = splitext(project_file)
	return project_name

def get_project_list():
	return [(get_project_name(window.project_file_name()), window.project_data()) for window in sublime.windows() if window.project_file_name()]

def sync_projects():
	global projects
	project_list = get_project_list()

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
				projects[project_name] = {"project_data": project_data, "beans": {}}
	# now that projects dict is up to date release lock before initing directory load
	for project_name, project_data in project_list:
		if project_name in new_project_names:
			load_project_async(project_name, project_data)

def load_project_async(project_name, project_data):
	sublime.set_timeout_async(partial(load_project, project_name, project_data))

def load_project(project_name, project_data):
	model_completion_folders = project_data.get("model_completion_folders", [])
	if len(model_completion_folders) == 0:
		return

	start_time = time.clock()
	file_count = 0
	project_beans = {}
	print("CFML: indexing project '" + project_name + "'" )

	for path in model_completion_folders:
		# normalize path
		path = path.replace("\\","/")
		if path[-1] == "/":
			path = path[:-1]
		beans, count = load_directory(path)
		project_beans.update(beans)
		file_count += count
	projects[project_name] = {"project_data": project_data, "beans": project_beans}
	print("CFML: indexing project '" + project_name + "' completed - " + str(file_count) + " files indexed in " + "{0:.2f}".format(time.clock() - start_time) + " seconds")

def load_project_file(project_file_name, project_data, file_path, bean_names=None):
	project_name = get_project_name(project_file_name)

	# check for tracked file path
	model_completion_folders = project_data.get("model_completion_folders", [])
	for root_path in model_completion_folders:
		# normalize root_path
		root_path = root_path.replace("\\","/")
		if root_path[-1] != "/":
			root_path = root_path + "/"
		if file_path.replace("\\","/").startswith(root_path):
			# check for bean names
			if not bean_names:
				bean_names = get_bean_names(root_path, file_path)
			file_metadata = load_file(file_path, bean_names)
			# lock for setting file completions
			with lock:
				if project_name not in projects:
					projects[project_name] = {"project_data": project_data, "beans": {}}
				projects[project_name]["beans"].update(file_metadata)

def has_bean(project_file_name, bean_name):
	project_name = get_project_name(project_file_name)
	if project_name in projects:
		return bean_name.lower() in projects[project_name]["beans"]
	return False

def get_bean(project_file_name, bean_name):
	return projects[get_project_name(project_file_name)]["beans"][bean_name.lower()]

def get_dot_completions(view, prefix, position, info):
	#are we in a project
	project_file_name = view.window().project_file_name()
	if project_file_name:
		# get context
		for symbol in info["dot_context"]:
			if not symbol.is_function:
				if has_bean(project_file_name, symbol.name):
					return CompletionList(get_bean(project_file_name, symbol.name).completions, 1, True)
				break

	return None

def on_navigate(view, file_path, symbol, href):
	index_locations = view.window().lookup_symbol_in_index(symbol)
	if file_path[1] == ":":
		file_path = "/" + file_path[0] + file_path[2:]
	for full_path, project_path, rowcol in index_locations:
		if full_path == file_path:
			row, col = rowcol
			view.window().open_file(full_path + ":" + str(row) + ":" + str(col), sublime.ENCODED_POSITION | sublime.FORCE_GROUP)

def get_inline_documentation(view, position):

	project_file_name = view.window().project_file_name()
	if project_file_name and view.match_selector(position, "meta.function-call.method"):
		function_name, function_name_region, function_args_region = utils.get_function_call(view, position)
		if view.substr(function_name_region.begin() - 1) == ".":
			dot_context = utils.get_dot_context(view, function_name_region.begin() - 1)
			for symbol in dot_context:
				if not symbol.is_function:
					if has_bean(project_file_name, symbol.name):
						bean = get_bean(project_file_name, symbol.name)
						if function_name in bean.functions:
							bean_function_name, bean_function_metadata = bean.functions[function_name]
							doc = get_documentation(symbol.name, bean.file_path, bean_function_name, bean_function_metadata)
							callback = partial(on_navigate, view, bean.file_path, bean_function_name)
							return Documentation(doc, callback, 2)
					break

	return None
