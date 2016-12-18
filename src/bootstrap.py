from . import applicationcfc
from . import basecompletions
from . import completions
from . import dotpaths
from . import cfdocs
from . import cfcs
from . import custom_tags
from . import entities
from . import fw1
from . import in_file_completions
from . import inline_documentation
from . import testbox
from .cfcs import CfmlDiPropertyCommand
from .cfc_dotted_path import CfmlCfcDottedPathCommand, CfmlSidebarCfcDottedPathCommand
from .completions import CfmlUpdateCompletionDocCommand
from .controller_view_toggle import CfmlToggleControllerViewCommand
from .color_scheme_styles import CfmlColorSchemeStylesCommand
from .goto_cfml_file import CfmlGotoFileCommand
from .index_project_command import CfmlIndexProjectCommand
from .inline_documentation import CfmlInlineDocumentationCommand
from .testbox import TestboxCommand
from .model_index import CfmlNavigateToMethodCommand
from .formatting.cfml_format import CfmlFormatCommand, CfmlFormatMenuCommand


def _plugin_loaded():
    inline_documentation._plugin_loaded()
    testbox._plugin_loaded()
