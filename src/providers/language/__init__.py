from ..provider import Provider
from . import language
from ...cfml_view import ContextType


provider = Provider(
    completions={
        ContextType.SCRIPT: language.get_script_completions,
        ContextType.DOT: language.get_dot_completions,
        ContextType.TAG_ATTRIBUTES: language.get_tag_attributes,
        ContextType.TAG: language.get_tags,
    },
    inline_documentation=language.get_inline_documentation,
    load=language.load_completions,
)
