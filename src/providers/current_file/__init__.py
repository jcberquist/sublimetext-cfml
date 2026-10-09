from ..provider import Provider
from . import completions
from .documentation import (
    get_inline_documentation,
    get_goto_cfml_file,
    get_completion_docs,
    get_method_preview,
)
from ...cfml_view import ContextType


provider = Provider(
    completions={
        ContextType.SCRIPT: completions.get_script_completions,
        ContextType.DOT: completions.get_dot_completions,
    },
    completion_docs=get_completion_docs,
    goto_cfml_file=get_goto_cfml_file,
    inline_documentation=get_inline_documentation,
    method_preview=get_method_preview,
)
