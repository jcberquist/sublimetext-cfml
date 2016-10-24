from .completions import build_project_entities, get_script_completions, get_dot_completions
from .documentation import get_inline_documentation, get_goto_cfml_file, get_completions_doc
from .. import completions, inline_documentation, goto_cfml_file, model_index


def get_completions(cfml_view):
    if cfml_view.type == 'script':
        return get_script_completions(cfml_view)
    elif cfml_view.type == 'dot':
        return get_dot_completions(cfml_view)
    return None


completions.add_completion_source(get_completions)
completions.add_completion_doc_source(get_completions_doc)
inline_documentation.add_documentation_source(get_inline_documentation)
goto_cfml_file.add_goto_source(get_goto_cfml_file)
model_index.subscribe(build_project_entities)
