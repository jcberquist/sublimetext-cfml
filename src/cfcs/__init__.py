from .cfcs import build_project_cfcs
from .completions import get_dot_completions
from .documentation import get_inline_documentation, get_goto_cfml_file, get_completions_doc
from .di import CfmlDiPropertyCommand
from .. import completions, inline_documentation, goto_cfml_file, model_index


def get_completions(cfml_view):
    if cfml_view.type == 'dot':
        return get_dot_completions(cfml_view)
    return None

completions.add_completion_source(get_completions)
completions.add_completion_doc_source(get_completions_doc)
inline_documentation.add_documentation_source(get_inline_documentation)
goto_cfml_file.add_goto_source(get_goto_cfml_file)
model_index.subscribe(build_project_cfcs)
