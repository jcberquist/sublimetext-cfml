from . import applicationcfc
from . import basecompletions
from . import completions
from . import component_index
from . import dotpaths
from . import cfdocs
from . import cfcs
from . import custom_tags
from . import entities
from . import fw1
from . import in_file_completions
from . import inline_documentation
from . import method_preview
from . import testbox
from .cfcs import CfmlDiPropertyCommand
from .cfc_dotted_path import CfmlCfcDottedPathCommand, CfmlSidebarCfcDottedPathCommand
from .completions import CfmlUpdateCompletionDocCommand
from .controller_view_toggle import CfmlToggleControllerViewCommand
from .color_scheme_styles import CfmlColorSchemeStylesCommand
from .goto_cfml_file import CfmlGotoFileCommand
from .index_project_command import CfmlIndexProjectCommand
from .inline_documentation import CfmlInlineDocumentationCommand
from .method_preview import CfmlPreviewMethodCommand
from .testbox import TestboxCommand, TestboxSpecOutlineCommand
from .component_index import CfmlNavigateToMethodCommand
from .formatting.cfml_format import CfmlFormatCommand


def _plugin_loaded():
    applicationcfc._plugin_loaded()
    basecompletions._plugin_loaded()
    component_index._plugin_loaded()
    custom_tags._plugin_loaded()
    fw1._plugin_loaded()
    inline_documentation._plugin_loaded()
    method_preview._plugin_loaded()
    testbox._plugin_loaded()
