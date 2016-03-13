import sublime
from .. import events
from .. import utils
from .component_project_index import *
from .documentation import get_documentation, get_method_documentation

__all__ = ["get_completions_by_dot_path", "get_completions_by_file_path",
"get_documentation", "get_dot_paths", "get_extended_metadata_by_file_path",
"get_file_path_by_dot_path", "get_file_paths", "get_metadata_by_dot_path",
"get_metadata_by_file_path", "get_method_documentation", "get_project_data",
"subscribe"]

def plugin_loaded():
	component_index.sync_projects()

def subscribe(listener):
	component_index.subscribe(listener)
