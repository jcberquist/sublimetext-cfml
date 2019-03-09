import sublime
from . import fw1
from .. import plugin


class CFMLPlugin(plugin.CFMLPlugin):
    def get_completions(self, cfml_view):
        if cfml_view.type == "script":
            return fw1.get_script_completions(cfml_view)
        elif cfml_view.type == "dot":
            return fw1.get_dot_completions(cfml_view)
        return None

    def get_inline_documentation(self, cfml_view, doc_type):
        return fw1.get_inline_documentation(cfml_view, doc_type)


def _plugin_loaded():
    sublime.set_timeout_async(fw1.load)
