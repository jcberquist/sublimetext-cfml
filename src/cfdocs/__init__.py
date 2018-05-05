from .cfdocs import get_inline_documentation, get_completion_docs, get_goto_cfml_file, get_cfdoc
from .. import completions, inline_documentation, goto_cfml_file


inline_documentation.add_documentation_source(get_inline_documentation)
completions.add_completion_doc_source(get_completion_docs)
goto_cfml_file.add_goto_source(get_goto_cfml_file)
