import sublime_plugin
from os.path import dirname, realpath
from .cfdocs import get_inline_documentation
from .. import inline_documentation

inline_documentation.add_documentation_source(get_inline_documentation)