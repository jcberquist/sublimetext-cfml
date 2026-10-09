"""
The kinds of the package's completions. A kind gives a completion its icon,
with the letter in it, and names what is completed.
"""

import sublime

FUNCTION = (sublime.KindId.FUNCTION, 'f', 'function')
METHOD = (sublime.KindId.FUNCTION, 'm', 'method')
ARGUMENT = (sublime.KindId.VARIABLE, 'a', 'argument')
VARIABLE = (sublime.KindId.VARIABLE, 'v', 'variable')
SETTING = (sublime.KindId.VARIABLE, 's', 'setting')
COMPONENT = (sublime.KindId.TYPE, 'c', 'component')
ENTITY = (sublime.KindId.TYPE, 'e', 'entity')
PACKAGE = (sublime.KindId.NAMESPACE, 'p', 'package')
TAG = (sublime.KindId.MARKUP, 't', 'tag')
CUSTOM_TAG = (sublime.KindId.MARKUP, 't', 'custom tag')
CUSTOM_TAG_PREFIX = (sublime.KindId.NAMESPACE, 'p', 'prefix')
ATTRIBUTE = (sublime.KindId.MARKUP, 'a', 'attribute')
# of a tag attribute or a function argument
VALUE = (sublime.KindId.AMBIGUOUS, 'v', 'value')
