import sublime
from .. import completions, inline_documentation
from . import basecompletions

def plugin_loaded():
	sublime.set_timeout_async(load)

def load():
    basecompletions.load_completions()
    completions.add_completion_source('tag', basecompletions.get_tags)
    completions.add_completion_source('tag_attributes', basecompletions.get_tag_attributes)
    completions.add_completion_source('script', basecompletions.get_script_completions)
    completions.add_completion_source('dot', basecompletions.get_dot_completions)
    inline_documentation.add_documentation_source(basecompletions.get_inline_documentation)
