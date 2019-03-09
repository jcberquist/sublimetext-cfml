from .. import plugin

from .cfdocs import (
    get_inline_documentation,
    get_completion_docs,
    get_goto_cfml_file
)


class CFMLPlugin(plugin.CFMLPlugin):
    def get_completion_docs(self, cfml_view):
        return get_completion_docs(cfml_view)

    def get_inline_documentation(self, cfml_view, doc_type):
        return get_inline_documentation(cfml_view, doc_type)

    def get_goto_cfml_file(self, cfml_view):
        return get_goto_cfml_file(cfml_view)
