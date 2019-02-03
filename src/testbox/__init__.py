from . import test_runner
from . import testbox
from .test_runner import TestboxCommand
from .testbox_spec_outline import TestboxSpecOutlineCommand
from .. import completions, inline_documentation


def _plugin_loaded():
    test_runner._plugin_loaded()
    testbox._plugin_loaded()


def get_completions(cfml_completions):
    if cfml_completions.type == 'script':
        return testbox.get_script_completions(cfml_completions)
    elif cfml_completions.type == 'dot':
        return testbox.get_dot_completions(cfml_completions)
    return None


completions.add_completion_source(get_completions)
inline_documentation.add_documentation_source(testbox.get_inline_documentation)
