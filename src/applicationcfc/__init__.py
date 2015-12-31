from .appcfc import get_dot_completions, get_script_completions, get_inline_documentation
from .. import completions, inline_documentation

completions.add_completion_source('script', get_script_completions)
completions.add_completion_source('dot', get_dot_completions)
inline_documentation.add_documentation_source(get_inline_documentation)