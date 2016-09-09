import sublime
from .. import completions, inline_documentation
from . import basecompletions


def plugin_loaded():
    sublime.set_timeout_async(load)


def get_completions(cfml_view):
    if cfml_view.type == 'script':
        return basecompletions.get_script_completions(cfml_view)
    elif cfml_view.type == 'dot':
        return basecompletions.get_dot_completions(cfml_view)
    elif cfml_view.type == 'tag_attributes':
        return basecompletions.get_tag_attributes(cfml_view)
    elif cfml_view.type == 'tag':
        return basecompletions.get_tags(cfml_view)
    return None


def load():
    basecompletions.load_completions()
    completions.add_completion_source(get_completions)
    inline_documentation.add_documentation_source(basecompletions.get_inline_documentation)
