from ..provider import Provider

from .cfdocs import (
    get_inline_documentation,
    get_completion_docs,
    get_goto_cfml_file
)


provider = Provider(
    completion_docs=get_completion_docs,
    inline_documentation=get_inline_documentation,
    goto_cfml_file=get_goto_cfml_file,
)
