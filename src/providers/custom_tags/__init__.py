from .completions import get_tags, get_tag_attributes, get_goto_cfml_file
from .documentation import get_inline_documentation

from ..provider import Provider
from ...cfml_view import ContextType


provider = Provider(
    completions={
        ContextType.TAG: get_tags,
        ContextType.TAG_ATTRIBUTES: get_tag_attributes,
    },
    goto_cfml_file=get_goto_cfml_file,
    inline_documentation=get_inline_documentation,
)
