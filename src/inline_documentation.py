import itertools
import sublime
import sublime_plugin
import time
import uuid
import webbrowser
from functools import partial
from . import utils
from . import view_state
from . import minihtml
from . import cfml_providers
from .cfml_view import CfmlView
from .view_state import DocPopup


# a doc that loads after its request can still be shown for a hover this
# many seconds old, unless a newer doc request has been made in the view
HOVER_REFRESH_SECONDS = 3
doc_requests = itertools.count()


def get_inline_documentation(cfml_view, doc_type):
    docs = []

    for p in cfml_providers.providers:
        inline_doc = p.get_inline_documentation(cfml_view, doc_type)
        if inline_doc:
            docs.append(inline_doc)

    return docs


def on_navigate(view, doc_popup_id, href):
    # the popup's docs are read from the view state when a link is clicked:
    # update_popup() keeps the on_navigate of the first show_popup(), so a
    # completion doc popup can be showing other docs than it was shown with
    popup = view_state.get(view).doc_popup
    if not popup or popup.id != doc_popup_id:
        return
    new_index = minihtml.page_index(href)
    if new_index is not None:
        display_documentation(view, popup.docs, popup.doc_type, popup.pt, new_index)
    elif popup.docs[popup.index].on_navigate:
        popup.docs[popup.index].on_navigate(href)
    else:
        webbrowser.open_new_tab(href)


def on_hide(view, doc_region_id):
    state = view_state.get(view)
    if state.doc_popup and state.doc_popup.id == doc_region_id:
        state.doc_popup = None
    view.erase_regions(doc_region_id)


def generate_documentation(view, docs, current_index, doc_type):
    doc = docs[current_index]
    build_page = (
        minihtml.completion_doc_page
        if doc_type == "completion_doc"
        else minihtml.doc_page
    )
    return build_page(view, doc.content, current_index, len(docs)), doc.doc_regions


def display_documentation(view, docs, doc_type, pt=-1, current_index=0):
    state = view_state.get(view)
    doc_region_id = str(uuid.uuid4())
    doc_html, doc_regions = generate_documentation(view, docs, current_index, doc_type)

    if doc_type == "completion_doc":
        popup = state.doc_popup
        if popup and popup.doc_type == "completion_doc" and view.is_popup_visible():
            state.doc_popup = DocPopup(popup.id, doc_type, docs, current_index, pt)
            view.update_popup(doc_html)
        else:
            state.doc_popup = DocPopup(doc_region_id, doc_type, docs, current_index, pt)
            view.show_popup(
                doc_html,
                flags=sublime.PopupFlags.COOPERATE_WITH_AUTO_COMPLETE,
                max_width=480,
                on_navigate=partial(on_navigate, view, doc_region_id),
                on_hide=lambda: on_hide(view, doc_region_id),
            )
    else:
        if doc_regions and utils.get_setting("inline_doc_regions_highlight"):
            view.add_regions(
                doc_region_id,
                utils.merge_regions(doc_regions),
                "source",
                flags=sublime.RegionFlags.DRAW_NO_FILL,
            )
        state.doc_popup = DocPopup(doc_region_id, doc_type, docs, current_index, pt)
        flags = (
            sublime.PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY
            if doc_type == "hover_doc"
            else sublime.PopupFlags.NONE
        )
        view.show_popup(
            doc_html,
            location=pt,
            flags=flags,
            max_width=768,
            max_height=480,
            on_navigate=partial(on_navigate, view, doc_region_id),
            on_hide=lambda: on_hide(view, doc_region_id),
        )


def show_inline_documentation(view, position, doc_type, can_refresh=True):
    request = view_state.get(view).doc_request = next(doc_requests)

    cfml_view = CfmlView(view, position)
    if can_refresh:
        cfml_view.on_data_loaded = partial(
            refresh_inline_documentation, view, position, doc_type, request, time.time()
        )

    docs = get_inline_documentation(cfml_view, doc_type)
    if len(docs) > 0:
        display_documentation(
            view,
            sorted(docs, key=lambda doc: doc.priority, reverse=True),
            doc_type,
            position,
        )


def refresh_inline_documentation(view, position, doc_type, request, requested_at):
    if not view.is_valid() or request != view_state.get(view).doc_request:
        return
    if doc_type == "hover_doc":
        if time.time() - requested_at > HOVER_REFRESH_SECONDS:
            return
    elif len(view.sel()) == 0 or view.sel()[0].begin() != position:
        return
    show_inline_documentation(view, position, doc_type, can_refresh=False)


class CfmlInlineDocumentationCommand(sublime_plugin.TextCommand):
    def run(self, edit, doc_type="inline_doc", pt=None):
        if doc_type == "hover_doc":
            if not utils.get_setting("cfml_hover_docs"):
                return
            if view_state.get(self.view).preview:
                return

        tick = time.time()
        position = pt if pt else self.view.sel()[0].begin()
        show_inline_documentation(self.view, position, doc_type)
        diff = time.time() - tick
        if utils.get_setting("cfml_log_doc_time"):
            print(
                "CFML: inline documentation completed in "
                + f"{diff * 1000:.0f}"
                + "ms"
            )
