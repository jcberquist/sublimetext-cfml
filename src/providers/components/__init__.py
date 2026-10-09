from . import components, dot_path_completions
from ..provider import Provider
from ...cfml_view import ContextType


provider = Provider(
    completions={
        ContextType.SCRIPT: components.get_script_completions,
        ContextType.DOT: components.get_dot_completions,
        ContextType.TAG_ATTRIBUTES: dot_path_completions.get_tag_attributes,
    },
    completion_docs=components.get_completion_docs,
    goto_cfml_file=components.get_goto_cfml_file,
    inline_documentation=components.get_inline_documentation,
    method_preview=components.get_method_preview,
    component_index_listener=components.build_project,
)
