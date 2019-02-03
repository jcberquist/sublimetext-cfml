import sublime
from .fw1 import (
    get_dot_completions,
    get_script_completions,
    get_inline_documentation,
    load
)
from .. import completions, inline_documentation


def _plugin_loaded():
    sublime.set_timeout_async(load)


def get_completions(cfml_view):
    if cfml_view.type == 'script':
        return get_script_completions(cfml_view)
    elif cfml_view.type == 'dot':
        return get_dot_completions(cfml_view)
    return None


completions.add_completion_source(get_completions)
inline_documentation.add_documentation_source(get_inline_documentation)
