from .completions import (
    build_project_map,
    get_script_completions,
    get_dot_completions,
    get_tag_attributes,
)
from .documentation import (
    get_inline_documentation,
    get_goto_cfml_file,
    get_completions_doc,
    get_method_preview,
)
from ...component_index import component_index

from .. import plugin


class CFMLPlugin(plugin.CFMLPlugin):
    def get_completion_docs(self, cfml_view):
        return get_completions_doc(cfml_view)

    def get_completions(self, cfml_view):
        if cfml_view.type == "script":
            return get_script_completions(cfml_view)
        elif cfml_view.type == "dot":
            return get_dot_completions(cfml_view)
        elif cfml_view.type == "tag_attributes":
            return get_tag_attributes(cfml_view)
        return None

    def get_goto_cfml_file(self, cfml_view):
        return get_goto_cfml_file(cfml_view)

    def get_inline_documentation(self, cfml_view, doc_type):
        return get_inline_documentation(cfml_view, doc_type)

    def get_method_preview(self, cfml_view):
        return get_method_preview(cfml_view)


component_index.subscribe(build_project_map)
