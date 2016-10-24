import sublime
from .component_project_index import *
from .documentation import get_documentation, build_documentation
from .documentation import get_method_documentation, build_method_documentation
from .documentation import get_function_call_params_doc, build_function_call_params_doc
from .navigate_to_method import CfmlNavigateToMethodCommand

__all__ = [
    "build_documentation",
    "build_function_call_params_doc",
    "build_method_documentation",
    "CfmlNavigateToMethodCommand",
    "get_completions_by_dot_path",
    "get_completions_by_entity_name",
    "get_completions_by_file_path",
    "get_documentation",
    "get_dot_paths",
    "get_entities",
    "get_extended_metadata_by_file_path",
    "get_file_path_by_dot_path",
    "get_file_path_by_entity_name",
    "get_file_paths",
    "get_function_call_params_doc",
    "get_metadata_by_dot_path",
    "get_metadata_by_entity_name",
    "get_metadata_by_file_path",
    "get_method_documentation",
    "get_project_data",
    "resync_project",
    "subscribe"
 ]


def plugin_loaded():
    component_index.sync_projects()


def subscribe(listener):
    component_index.subscribe(listener)
