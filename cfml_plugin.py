import sublime
import sublime_plugin
from .src import completions, utils, _plugin_loaded, _plugin_unloaded

from .src.buffer_metadata import BufferMetadata
from .src.commands import (
    CfmlAutoInsertClosingTagCommand,
    CfmlCloseTagCommand,
    CfmlEditSettingsCommand,
)
from .src.commands.cfc_dotted_path import (
    CfmlCfcDottedPathCommand,
    CfmlSidebarCfcDottedPathCommand,
)
from .src.commands.color_scheme_styles import CfmlColorSchemeStylesCommand
from .src.commands.controller_view_toggle import CfmlToggleControllerViewCommand
from .src.commands.format import CfmlFormatCommand, CfmlReplaceTextCommand
from .src.completions import CfmlUpdateCompletionDocCommand
from .src.component_index.commands import (
    CfmlClearIndexCacheCommand,
    CfmlIndexProjectCommand,
)
from .src.component_index.navigate_to_method import CfmlNavigateToMethodCommand
from .src.goto_cfml_file import CfmlGotoFileCommand
from .src.inline_documentation import CfmlInlineDocumentationCommand
from .src.method_preview import CfmlPreviewMethodCommand
from .src.providers.components.di import CfmlDiPropertyCommand
from .src.providers.testbox.test_runner import TestboxCommand
from .src.providers.testbox.testbox_spec_outline import TestboxSpecOutlineCommand
from .src.project_watcher import ProjectEventListener
from .src.view_state import ViewState

# Sublime Text registers the commands and listeners it finds in this module
__all__ = [
    "BufferMetadata",
    "CfmlAutoInsertClosingTagCommand",
    "CfmlCfcDottedPathCommand",
    "CfmlClearIndexCacheCommand",
    "CfmlCloseTagCommand",
    "CfmlColorSchemeStylesCommand",
    "CfmlDiPropertyCommand",
    "CfmlEditSettingsCommand",
    "CfmlFormatCommand",
    "CfmlGotoFileCommand",
    "CfmlIndexProjectCommand",
    "CfmlInlineDocumentationCommand",
    "CfmlNavigateToMethodCommand",
    "CfmlPreviewMethodCommand",
    "CfmlReplaceTextCommand",
    "CfmlSidebarCfcDottedPathCommand",
    "CfmlToggleControllerViewCommand",
    "CfmlUpdateCompletionDocCommand",
    "CfmlViewListener",
    "ProjectEventListener",
    "TestboxCommand",
    "TestboxSpecOutlineCommand",
    "ViewState",
    "plugin_loaded",
    "plugin_unloaded",
]


def plugin_loaded():
    _plugin_loaded()


def plugin_unloaded():
    _plugin_unloaded()


class CfmlViewListener(sublime_plugin.ViewEventListener):
    """
    Completions and hover docs. Sublime Text creates one for each view with
    the CFML syntax, so views of other syntaxes never call into the package.
    """

    @classmethod
    def is_applicable(cls, settings):
        return utils.is_cfml_view(settings)

    @classmethod
    def applies_to_primary_view_only(cls):
        return False

    def on_post_text_command(self, command_name, args):
        if command_name == "commit_completion":
            view = self.view
            pos = view.sel()[0].begin()

            if view.match_selector(
                pos,
                "meta.tag.cfml -source.cfml.script, meta.tag.script.cfml, meta.tag.script.cf.cfml, meta.class.declaration.cfml -meta.class.inheritance.cfml",
            ):
                if view.substr(pos - 1) in [" ", '"', "'", "="]:
                    view.run_command("auto_complete", {"api_completions_only": True})
                elif view.substr(pos) == '"':
                    # an attribute completion was most likely just inserted
                    # advance cursor past double quote character
                    view.run_command("move", {"by": "characters", "forward": True})

            if view.substr(pos - 1) == ":" and view.match_selector(
                pos - 1, "meta.tag.custom.cfml -source.cfml.script"
            ):
                view.run_command("auto_complete", {"api_completions_only": True})

            if view.substr(pos - 1) == "." and view.match_selector(
                pos - 1,
                "meta.function-call.support.createcomponent.cfml string.quoted, entity.other.inherited-class.cfml, meta.instance.constructor.cfml",
            ):
                view.run_command("auto_complete", {"api_completions_only": True})

    def on_query_completions(self, prefix, locations):
        return completions.get_completions(self.view, locations[0], prefix)

    def on_hover(self, point, hover_zone):
        if hover_zone != sublime.HoverZone.TEXT:
            return

        self.view.run_command(
            "cfml_inline_documentation", {"pt": point, "doc_type": "hover_doc"}
        )
