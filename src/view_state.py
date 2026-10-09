import sublime
import sublime_plugin
from dataclasses import dataclass
from typing import Any
from . import utils


@dataclass
class DocPopup:
    """The doc popup showing in a view, as its on_navigate needs it."""

    # also the key of the regions it highlights; a late on_hide from an
    # older popup is told apart by it
    id: str
    # 'inline_doc', 'hover_doc' or 'completion_doc'
    doc_type: str
    docs: list[Any]
    # the doc on show
    index: int
    # where the docs were shown for
    pt: int


class ViewState(sublime_plugin.ViewEventListener):
    """
    What the package keeps for a view. As a view event listener it has the
    lifetime of its view: Sublime Text creates one for each CFML view, and
    drops it when the view closes or gets another syntax.
    """

    @classmethod
    def is_applicable(cls, settings):
        return utils.is_cfml_view(settings)

    @classmethod
    def applies_to_primary_view_only(cls):
        return False

    def __init__(self, view):
        super().__init__(view)
        self.doc_popup: DocPopup | None = None
        # the latest doc request, so a doc that loads later is shown only
        # for it
        self.doc_request: int | None = None
        # the method preview phantom set and the point it was opened for
        self.preview: tuple[Any, int] | None = None

    def close_preview(self):
        if self.preview:
            self.view.erase_phantoms(PREVIEW_KEY)
            self.view.erase_regions(PREVIEW_KEY)
            self.preview = None

    def close(self):
        """Removes what the package is showing in the view."""
        if self.doc_popup:
            self.view.hide_popup()
        self.close_preview()


# the key of the phantom and the regions of a method preview
PREVIEW_KEY = 'cfml_method_preview'


def get(view) -> ViewState:
    state = sublime_plugin.find_view_event_listener(view, ViewState)
    if isinstance(state, ViewState):
        return state
    # not a CFML view, so there is nothing to keep state for
    return ViewState(view)


def close_all():
    for window in sublime.windows():
        for view in window.views(include_transient=True):
            get(view).close()
