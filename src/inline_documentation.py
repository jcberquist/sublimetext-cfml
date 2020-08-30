import sublime
import sublime_plugin
import time
import uuid
import webbrowser
from . import utils
from . import method_preview
from . import minihtml
from . import cfml_plugins
from .cfml_view import CfmlView


DOC_TEMPLATE = ""
COMPLETION_DOC_TEMPLATE = ""
PAGINATION_TEMPLATE = ""


SELECTORS = [
    "constant.language",
    "entity.name.class",
    "entity.name.function",
    "entity.name.tag.cfml",
    "entity.other.attribute-name",
    "entity.other.inherited-class",
    "storage.modifier",
    "storage.type",
    "string.quoted",
    "variable.language",
    "variable.parameter.function",
]


doc_window = None


def get_inline_documentation(cfml_view, doc_type):
    docs = []

    for p in cfml_plugins.plugins:
        inline_doc = p.get_inline_documentation(cfml_view, doc_type)
        if inline_doc:
            docs.append(inline_doc)

    return docs


def _plugin_loaded():
    global DOC_TEMPLATE, COMPLETION_DOC_TEMPLATE, PAGINATION_TEMPLATE
    root_path = "Packages/" + utils.get_plugin_name() + "/templates"
    DOC_TEMPLATE = sublime.load_resource(
        root_path + "/inline_documentation.html"
    ).replace("\r", "")
    COMPLETION_DOC_TEMPLATE = sublime.load_resource(
        root_path + "/completion_doc.html"
    ).replace("\r", "")
    PAGINATION_TEMPLATE = sublime.load_resource(root_path + "/pagination.html").replace(
        "\r", ""
    )


def build_links(links):
    html_links = [
        '<a href="' + link["href"] + '">' + link["text"] + "</a>" for link in links
    ]
    return "<br>".join(html_links)


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


def build_doc_html(inline_doc, doc_type):
    template = DOC_TEMPLATE if doc_type != "completion_doc" else COMPLETION_DOC_TEMPLATE
    html = sublime.expand_variables(template, inline_doc)
    if doc_type == "completion_doc":
        html = html.replace('<div class="body"></div>', "")
    return html


def get_on_navigate(view, docs, doc_type, current_index, pt):
    def on_navigate(href):
        if href.startswith("page_"):
            new_index = int(href.split("_").pop())
            display_documentation(view, docs, doc_type, pt, new_index)
        elif docs[current_index].on_navigate:
            docs[current_index].on_navigate(href)
        else:
            webbrowser.open_new_tab(href)

    return on_navigate


def on_hide(view, doc_region_id):
    global doc_window
    doc_window = None
    view.erase_regions(doc_region_id)


def generate_documentation(view, docs, current_index, doc_type):
    doc_html_variables = dict(docs[current_index].doc_html_variables["html"])
    doc_html_variables["side_color"] = docs[current_index].doc_html_variables[
        "side_color"
    ]

    if "styles" in docs[current_index].doc_html_variables:
        doc_html_variables.update(docs[current_index].doc_html_variables["styles"])

    styles_by_selector = minihtml.get_selector_style_map(view, SELECTORS)
    for key in styles_by_selector:
        style = styles_by_selector[key]
        css = ""
        if "foreground" in style:
            css += "color: " + style["foreground"] + ";\n"
        if "italic" in style and style["italic"]:
            css += "font-style: italic;\n"
        doc_html_variables[key.replace(".", "_")] = css

    doc_html_variables["pagination"] = (
        build_pagination(current_index, len(docs)) if len(docs) > 1 else ""
    )
    doc_html_variables["links"] = (
        build_links(doc_html_variables["links"])
        if "links" in doc_html_variables
        else ""
    )

    return build_doc_html(doc_html_variables, doc_type), docs[current_index].doc_regions


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


def display_documentation(view, docs, doc_type, pt=-1, current_index=0):
    global doc_window
    doc_region_id = str(uuid.uuid4())
    doc_html, doc_regions = generate_documentation(view, docs, current_index, doc_type)
    on_navigate = get_on_navigate(view, docs, doc_type, current_index, pt)

    if doc_type == "completion_doc":
        if doc_window and doc_window == "completion_doc":
            view.update_popup(doc_html)
        else:
            doc_window = "completion_doc"
            view.show_popup(
                doc_html,
                flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
                max_width=480,
                on_navigate=on_navigate,
                on_hide=lambda: on_hide(view, doc_region_id),
            )
    else:
        if doc_regions and utils.get_setting("inline_doc_regions_highlight"):
            view.add_regions(
                doc_region_id,
                merge_regions(doc_regions),
                "source",
                flags=sublime.DRAW_NO_FILL,
            )
        doc_window = "inline_doc"
        flags = sublime.HIDE_ON_MOUSE_MOVE_AWAY if doc_type == "hover_doc" else 0
        # print(doc_html)
        view.show_popup(
            doc_html,
            location=pt,
            flags=flags,
            max_width=768,
            max_height=480,
            on_navigate=on_navigate,
            on_hide=lambda: on_hide(view, doc_region_id),
        )


class CfmlInlineDocumentationCommand(sublime_plugin.TextCommand):
    def run(self, edit, doc_type="inline_doc", pt=None):
        if doc_type == "hover_doc":
            if not utils.get_setting("cfml_hover_docs"):
                return
            if self.view.buffer_id() in method_preview.phantom_sets_by_buffer:
                return

        tick = time.time()
        position = pt if pt else self.view.sel()[0].begin()
        cfml_view = CfmlView(self.view, position)
        docs = get_inline_documentation(cfml_view, doc_type)
        if len(docs) > 0:
            display_documentation(
                self.view,
                sorted(docs, key=lambda doc: doc.priority, reverse=True),
                doc_type,
                position,
            )
        diff = time.time() - tick
        if utils.get_setting("cfml_log_doc_time"):
            print(
                "CFML: inline documentation completed in "
                + "{:.0f}".format(diff * 1000)
                + "ms"
            )
