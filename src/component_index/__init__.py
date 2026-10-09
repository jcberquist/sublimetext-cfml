from . import documentation
from .index import ComponentIndex
from .completions import build_file_completions, to_completion_item


__all__ = [
    "build_file_completions",
    "component_index",
    "documentation",
    "to_completion_item",
]


# the one index, named as the package: `from .component_index import component_index`
component_index: ComponentIndex = ComponentIndex()


def _plugin_loaded():
    component_index.init_parser()
