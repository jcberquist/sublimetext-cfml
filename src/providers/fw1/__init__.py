import sublime
from functools import partial
from . import fw1
from ..provider import Provider
from ...cfml_view import ContextType


provider = Provider(
    completions={
        ContextType.SCRIPT: fw1.get_script_completions,
        ContextType.DOT: fw1.get_dot_completions,
    },
    inline_documentation=fw1.get_inline_documentation,
    load=partial(sublime.set_timeout_async, fw1.load),
)
