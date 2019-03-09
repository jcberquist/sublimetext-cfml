from .. import plugin
from . import in_file_completions
from .documentation import (
    get_inline_documentation,
    get_goto_cfml_file,
    get_completion_docs,
    get_method_preview,
)


class CFMLPlugin(plugin.CFMLPlugin):
    def get_completion_docs(self, cfml_view):
        return get_completion_docs(cfml_view)

    def get_completions(self, cfml_view):
        if cfml_view.type == "script":
            return in_file_completions.get_script_completions(cfml_view)
        elif cfml_view.type == "dot":
            return in_file_completions.get_dot_completions(cfml_view)
        return None

    def get_goto_cfml_file(self, cfml_view):
        return get_goto_cfml_file(cfml_view)

    def get_inline_documentation(self, cfml_view, doc_type):
        return get_inline_documentation(cfml_view, doc_type)

    def get_method_preview(self, cfml_view):
        return get_method_preview(cfml_view)
