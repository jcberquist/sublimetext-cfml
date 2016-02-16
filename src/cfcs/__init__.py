from .cfcs import build_project_cfcs
from .completions import get_dot_completions
from .documentation import get_inline_documentation, get_goto_cfc
from .. import completions, inline_documentation, goto_cfc, model_index

completions.add_completion_source('dot', get_dot_completions)
inline_documentation.add_documentation_source(get_inline_documentation)
goto_cfc.add_goto_source(get_goto_cfc)
model_index.subscribe(build_project_cfcs)
