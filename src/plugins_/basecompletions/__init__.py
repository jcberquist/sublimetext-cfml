from .. import plugin
from . import basecompletions


class CFMLPlugin(plugin.CFMLPlugin):
    def get_completions(self, cfml_view):
        if cfml_view.type == "script":
            return basecompletions.get_script_completions(cfml_view)
        elif cfml_view.type == "dot":
            return basecompletions.get_dot_completions(cfml_view)
        elif cfml_view.type == "tag_attributes":
            return basecompletions.get_tag_attributes(cfml_view)
        elif cfml_view.type == "tag":
            return basecompletions.get_tags(cfml_view)
        return None

    def get_inline_documentation(self, cfml_view, doc_type):
        return basecompletions.get_inline_documentation(cfml_view, doc_type)


def _plugin_loaded():
    basecompletions.load_completions()
