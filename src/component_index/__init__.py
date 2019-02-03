from collections import namedtuple
from .component_index import ComponentIndex
from .documentation import (
    build_documentation,
    build_method_documentation,
    build_method_preview,
    build_method_preview_doc,
    build_function_call_params_doc,
)
from .completions import build_file_completions
from .navigate_to_method import CfmlNavigateToMethodCommand


__all__ = ["CfmlNavigateToMethodCommand", "builders", "component_index"]


build_functions = [
    "build_documentation",
    "build_method_documentation",
    "build_method_preview",
    "build_method_preview_doc",
    "build_function_call_params_doc",
    "build_file_completions",
]


Builders = namedtuple("Builders", build_functions)


component_index = ComponentIndex()
builders = Builders(
    build_documentation,
    build_method_documentation,
    build_method_preview,
    build_method_preview_doc,
    build_function_call_params_doc,
    build_file_completions,
)


def _plugin_loaded():
    component_index.init_parser()
    component_index.sync_projects()
