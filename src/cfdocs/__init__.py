from .cfdocs import get_inline_documentation, get_completion_docs
from .. import completions
from .. import inline_documentation

inline_documentation.add_documentation_source(get_inline_documentation)
completions.add_completion_doc_source(get_completion_docs)
