from .completions import get_completions, get_goto_cfml_file
from .documentation import get_inline_documentation

from .. import plugin


class CFMLPlugin(plugin.CFMLPlugin):
    def get_completions(self, cfml_view):
        return get_completions(cfml_view)

    def get_goto_cfml_file(self, cfml_view):
        return get_goto_cfml_file(cfml_view)

    def get_inline_documentation(self, cfml_view, doc_type):
        return get_inline_documentation(cfml_view, doc_type)
