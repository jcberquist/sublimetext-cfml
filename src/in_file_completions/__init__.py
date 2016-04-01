from .. import completions, inline_documentation, goto_cfml_file
from . import in_file_completions
from .documentation import get_inline_documentation, get_goto_cfml_file

completions.add_completion_source('script', in_file_completions.get_script_completions)
completions.add_completion_source('dot', in_file_completions.get_dot_completions)
inline_documentation.add_documentation_source(get_inline_documentation)
goto_cfml_file.add_goto_source(get_goto_cfml_file)
