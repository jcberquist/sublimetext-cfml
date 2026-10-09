import sublime
from functools import partial
from . import testbox
from ..provider import Provider
from ...cfml_view import ContextType


provider = Provider(
    completions={
        ContextType.SCRIPT: testbox.get_script_completions,
        ContextType.DOT: testbox.get_dot_completions,
    },
    inline_documentation=testbox.get_inline_documentation,
    load=partial(sublime.set_timeout_async, testbox.load),
)
