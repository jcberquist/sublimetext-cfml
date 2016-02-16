import sublime
from .. import events
from .. import utils
from .project_index import *
from .documentation import get_documentation, get_method_documentation

__all__ = ["get_completions_by_dot_path", "get_completions_by_file_path",
"get_documentation", "get_dot_paths", "get_extended_metadata_by_file_path",
"get_file_path_by_dot_path", "get_file_paths", "get_metadata_by_dot_path",
"get_metadata_by_file_path", "get_method_documentation", "get_project_data",
"subscribe"]

def plugin_loaded():
	sync_projects()

def on_post_save_async(view):
	file_name = view.file_name().replace("\\","/")
	# check to see if the updated file was a .sublime-project
	if file_name.lower().endswith(".sublime-project"):
		# trying this without try/catch so that errors show in the console
		project_name = utils.extract_project_name(file_name)
		project_data = sublime.decode_value(view.substr(sublime.Region(0, view.size())))
		project_updated(project_name, project_data)
	else:
		project_name = utils.get_project_name(view)
		if project_name:
			index_project_file(project_name, file_name)

def on_post_window_command(window, command, args):
	if command == "delete_file":
		window_project_name = utils.get_project_name_from_window(window)
		if window_project_name:
			for file_name in args["files"]:
				if not file_name.lower().endswith(".sublime-project"):
					remove_project_file(window_project_name, file_name.replace("\\","/"))

		for file_name in args["files"]:
			if file_name.lower().endswith(".sublime-project"):
				project_name = utils.extract_project_name(file_name)
				project_deleted(project_name)


events.subscribe('on_load_async', lambda view: sync_projects())
events.subscribe('on_close', lambda view: sync_projects())
events.subscribe('on_post_save_async', on_post_save_async)
events.subscribe('on_post_window_command', on_post_window_command)
