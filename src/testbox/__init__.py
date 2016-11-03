from .testbox import get_dot_completions, get_script_completions, get_inline_documentation
from . import test_runner
from .test_runner import TestboxCommand
from .. import completions, inline_documentation


def _plugin_loaded():
    test_runner._plugin_loaded()


def get_completions(cfml_completions):
    if cfml_completions.type == 'script':
        return get_script_completions(cfml_completions)
    elif cfml_completions.type == 'dot':
        return get_dot_completions(cfml_completions)
    return None

completions.add_completion_source(get_completions)
inline_documentation.add_documentation_source(get_inline_documentation)
