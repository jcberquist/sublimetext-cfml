import sublime
from functools import partial
from . import appcfc
from ..provider import Provider
from ...cfml_view import ContextType


provider = Provider(
    completions={
        ContextType.SCRIPT: appcfc.get_script_completions,
        ContextType.DOT: appcfc.get_dot_completions,
    },
    inline_documentation=appcfc.get_inline_documentation,
    load=partial(sublime.set_timeout_async, appcfc.load),
)
