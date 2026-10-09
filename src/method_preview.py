import sublime
import sublime_plugin
import webbrowser
from . import minihtml
from . import utils
from . import view_state
from . import cfml_providers
from .cfml_view import CfmlView



def get_method_previews(cfml_view):
    previews = []

    for p in cfml_providers.providers:
        preview = p.get_method_preview(cfml_view)
        if preview:
            previews.append(preview)

    return previews


def close_phantom(view):
    view_state.get(view).close_preview()


def get_on_navigate(view, docs, current_index, pt):
    def on_navigate(href):
        new_index = minihtml.page_index(href)
        if new_index is not None:
            display_previews(view, docs, pt, new_index)
        elif href == minihtml.CLOSE_HREF:
            close_phantom(view)
        elif docs[current_index].on_navigate:
            docs[current_index].on_navigate(href)
        else:
            webbrowser.open_new_tab(href)

    return on_navigate


def generate_previews(view, docs, current_index):
    preview = docs[current_index]
    html = minihtml.preview_page(view, preview.content, current_index, len(docs))
    return html, preview.preview_regions


def display_previews(view, previews, pt=-1, current_index=0):
    state = view_state.get(view)

    # paging only applies to the preview that is open
    if state.preview and pt != state.preview[1]:
        return

    preview_html, preview_regions = generate_previews(view, previews, current_index)
    on_navigate = get_on_navigate(view, previews, current_index, pt)
    view.add_regions(
        view_state.PREVIEW_KEY,
        utils.merge_regions(preview_regions),
        "source",
        flags=sublime.RegionFlags.DRAW_NO_FILL,
    )

    phantom_set = sublime.PhantomSet(view, view_state.PREVIEW_KEY)
    state.preview = (phantom_set, pt)
    phantom = sublime.Phantom(
        view.line(pt), preview_html, sublime.PhantomLayout.BLOCK, on_navigate
    )
    phantom_set.update([phantom])


class CfmlPreviewMethodCommand(sublime_plugin.TextCommand):
    def run(self, edit, pt=None):
        if view_state.get(self.view).preview:
            close_phantom(self.view)
            return

        position = pt if pt else self.view.sel()[0].begin()
        cfml_view = CfmlView(self.view, position)
        previews = get_method_previews(cfml_view)
        if len(previews) > 0:
            display_previews(
                self.view,
                sorted(previews, key=lambda doc: doc.priority, reverse=True),
                position,
            )
