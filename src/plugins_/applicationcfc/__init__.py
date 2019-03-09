import sublime
from . import appcfc
from .. import plugin


def _plugin_loaded():
    sublime.set_timeout_async(appcfc.load)


class CFMLPlugin(plugin.CFMLPlugin):
    def get_completions(self, cfml_view):
        if cfml_view.type == 'script':
            return appcfc.get_script_completions(cfml_view)
        elif cfml_view.type == 'dot':
            return appcfc.get_dot_completions(cfml_view)
        return None

    def get_inline_documentation(self, cfml_view, doc_type):
        return appcfc.get_inline_documentation(cfml_view, doc_type)
