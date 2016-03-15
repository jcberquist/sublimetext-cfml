from .completions import build_project_map, get_script_completions, get_dot_completions, get_tag_attributes
from .documentation import get_inline_documentation, get_goto_cfml_file
from .. import completions, inline_documentation, goto_cfml_file, model_index

completions.add_completion_source("script", get_script_completions)
completions.add_completion_source("dot", get_dot_completions)
completions.add_completion_source('tag_attributes', get_tag_attributes)
inline_documentation.add_documentation_source(get_inline_documentation)
goto_cfml_file.add_goto_source(get_goto_cfml_file)
model_index.subscribe(build_project_map)
