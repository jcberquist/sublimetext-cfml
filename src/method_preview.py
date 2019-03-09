import sublime
import sublime_plugin
import webbrowser
from . import utils
from . import cfml_plugins
from .cfml_view import CfmlView


PREVIEW_TEMPLATE = ""
PAGINATION_TEMPLATE = ""
phantom_sets_by_buffer = {}


def get_method_previews(cfml_view):
    previews = []

    for p in cfml_plugins.plugins:
        preview = p.get_method_preview(cfml_view)
        if preview:
            previews.append(preview)

    return previews


def _plugin_loaded():
    global PREVIEW_TEMPLATE, PAGINATION_TEMPLATE
    root_path = "Packages/" + utils.get_plugin_name() + "/templates"
    PREVIEW_TEMPLATE = sublime.load_resource(
        root_path + "/method_preview.html"
    ).replace("\r", "")
    PAGINATION_TEMPLATE = sublime.load_resource(root_path + "/pagination.html").replace(
        "\r", ""
    )


def build_pagination(current_index, total_pages):
    pagination_variables = {
        "current_page": str(current_index + 1),
        "total_pages": str(total_pages),
    }

    previous_index = current_index - 1 if current_index > 0 else total_pages - 1
    pagination_variables["prev"] = "page_" + str(previous_index)

    next_index = current_index + 1 if current_index < total_pages - 1 else 0
    pagination_variables["next"] = "page_" + str(next_index)

    return sublime.expand_variables(PAGINATION_TEMPLATE, pagination_variables)


def close_phantom(view):
    global phantom_sets_by_buffer
    buffer_id = view.buffer_id()
    if buffer_id in phantom_sets_by_buffer:
        view.erase_phantoms("cfml_method_preview")
        view.erase_regions("cfml_method_preview")
        del phantom_sets_by_buffer[buffer_id]


def get_on_navigate(view, docs, current_index, pt):
    def on_navigate(href):
        if href.startswith("page_"):
            new_index = int(href.split("_").pop())
            display_previews(view, docs, pt, new_index)
        elif href == "__close__":
            close_phantom(view)
        elif docs[current_index].on_navigate:
            docs[current_index].on_navigate(href)
        else:
            webbrowser.open_new_tab(href)

    return on_navigate


def generate_previews(docs, current_index):
    preview_html_variables = dict(docs[current_index].preview_html_variables["html"])
    preview_html_variables["pagination"] = (
        build_pagination(current_index, len(docs)) if len(docs) > 1 else ""
    )
    html = sublime.expand_variables(PREVIEW_TEMPLATE, preview_html_variables)
    return html, docs[current_index].preview_regions


def merge_regions(regions):
    merged_regions = []
    for region in sorted(regions):
        if len(merged_regions) > 0 and merged_regions[-1].contains(region):
            continue
        elif len(merged_regions) > 0 and merged_regions[-1].end() == region.begin():
            merged_regions[-1] = sublime.Region(
                merged_regions[-1].begin(), region.end()
            )
        else:
            merged_regions.append(region)
    return merged_regions


def display_previews(view, previews, pt=-1, current_index=0):
    global phantom_sets_by_buffer
    buffer_id = view.buffer_id()

    if (
        buffer_id in phantom_sets_by_buffer
        and pt != phantom_sets_by_buffer[buffer_id][1]
    ):
        return

    preview_html, preview_regions = generate_previews(previews, current_index)
    on_navigate = get_on_navigate(view, previews, current_index, pt)
    view.add_regions(
        "cfml_method_preview",
        merge_regions(preview_regions),
        "source",
        flags=sublime.DRAW_NO_FILL,
    )

    phantom_set = sublime.PhantomSet(view, "cfml_method_preview")
    phantom_sets_by_buffer[buffer_id] = (phantom_set, pt)
    phantom = sublime.Phantom(
        view.line(pt), preview_html, sublime.LAYOUT_BLOCK, on_navigate
    )
    phantom_set.update([phantom])


class CfmlPreviewMethodCommand(sublime_plugin.TextCommand):
    def run(self, edit, pt=None):
        buffer_id = self.view.buffer_id()
        if buffer_id in phantom_sets_by_buffer:
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
