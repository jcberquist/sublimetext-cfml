from . import test_runner
from . import testbox
from .test_runner import TestboxCommand
from .testbox_spec_outline import TestboxSpecOutlineCommand
from .. import plugin


class CFMLPlugin(plugin.CFMLPlugin):
    def get_completions(self, cfml_view):
        if cfml_view.type == "script":
            return testbox.get_script_completions(cfml_view)
        elif cfml_view.type == "dot":
            return testbox.get_dot_completions(cfml_view)
        return None

    def get_inline_documentation(self, cfml_view, doc_type):
        return testbox.get_inline_documentation(cfml_view, doc_type)


def _plugin_loaded():
    test_runner._plugin_loaded()
    testbox._plugin_loaded()
