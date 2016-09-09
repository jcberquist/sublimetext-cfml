from .. import completions, inline_documentation, goto_cfml_file
from . import in_file_completions
from .documentation import get_inline_documentation, get_goto_cfml_file


def get_completions(cfml_completions):
    if cfml_completions.type == 'script':
        return in_file_completions.get_script_completions(cfml_completions)
    elif cfml_completions.type == 'dot':
        return in_file_completions.get_dot_completions(cfml_completions)
    return None

completions.add_completion_source(get_completions)
inline_documentation.add_documentation_source(get_inline_documentation)
goto_cfml_file.add_goto_source(get_goto_cfml_file)
