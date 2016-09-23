import sublime
import sublime_plugin
import webbrowser
from . import utils
from .cfml_view import CfmlView

DOC_TEMPLATE = ""
COMPLETION_DOC_TEMPLATE = ""
PAGINATION_TEMPLATE = ""

doc_window = None
documentation_sources = []


def add_documentation_source(callback):
    documentation_sources.append(callback)


def get_inline_documentation(cfml_view):
    docs = []

    for callback in documentation_sources:
        inline_doc = callback(cfml_view)
        if inline_doc:
            docs.append(inline_doc)

    return docs


def _plugin_loaded():
    global DOC_TEMPLATE, COMPLETION_DOC_TEMPLATE, PAGINATION_TEMPLATE
    root_path = "Packages/" + utils.get_plugin_name() + "/templates"
    DOC_TEMPLATE = sublime.load_resource(root_path + "/inline_documentation.html").replace("\r", "")
    COMPLETION_DOC_TEMPLATE = sublime.load_resource(root_path + "/completion_doc.html").replace("\r", "")
    PAGINATION_TEMPLATE = sublime.load_resource(root_path + "/pagination.html").replace("\r", "")


def build_links(links):
    html_links = ['<a class="link" href="' + link["href"] + '">' + link["text"] + '</a>' for link in links]
    return "<br>".join(html_links)


def build_pagination(current_index, total_pages):
    pagination_variables = {"current_page": str(current_index + 1), "total_pages": str(total_pages)}

    previous_index = current_index - 1 if current_index > 0 else total_pages - 1
    pagination_variables["prev"] = "page_" + str(previous_index)

    next_index = current_index + 1 if current_index < total_pages - 1 else 0
    pagination_variables["next"] = "page_" + str(next_index)

    return sublime.expand_variables(PAGINATION_TEMPLATE, pagination_variables)


def build_doc_html(inline_doc, completion_doc):
    template = DOC_TEMPLATE if not completion_doc else COMPLETION_DOC_TEMPLATE
    return sublime.expand_variables(template, inline_doc)


def get_on_navigate(view, docs, current_index, completion_doc):
    def on_navigate(href):
        if href.startswith("page_"):
            new_index = int(href.split("_").pop())
            display_documentation(view, docs, new_index, completion_doc)
        elif docs[current_index].on_navigate:
            docs[current_index].on_navigate(href)
        else:
            webbrowser.open_new_tab(href)
    return on_navigate


def on_hide():
    global doc_window
    doc_window = None


def generate_documentation(docs, current_index, completion_doc):
    doc_html_variables = dict(docs[current_index].doc_html_variables)
    doc_html_variables["pagination"] = build_pagination(current_index, len(docs)) if len(docs) > 1 else ""
    doc_html_variables["links"] = build_links(doc_html_variables["links"]) if "links" in doc_html_variables else ""

    return build_doc_html(doc_html_variables, completion_doc)


def display_documentation(view, docs, current_index=0, completion_doc=False):
    global doc_window
    doc_html = generate_documentation(docs, current_index, completion_doc)
    on_navigate = get_on_navigate(view, docs, current_index, completion_doc)
    if completion_doc:
        # print(doc_html)
        if doc_window and doc_window == "completion_doc":
            view.update_popup(doc_html)
        else:
            doc_window = "completion_doc"
            view.show_popup(doc_html, flags=sublime.COOPERATE_WITH_AUTO_COMPLETE, on_navigate=on_navigate, on_hide=on_hide)
    else:
        if doc_window and doc_window == "inline_doc":
            view.update_popup(doc_html)
        else:
            doc_window = "inline_doc"
            view.show_popup(doc_html, max_width=1024, max_height=480, on_navigate=on_navigate, on_hide=on_hide)


class CfmlInlineDocumentationCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        position = self.view.sel()[0].begin()
        cfml_view = CfmlView(self.view, position)
        docs = get_inline_documentation(cfml_view)
        if len(docs) > 0:
            display_documentation(self.view, sorted(docs, key=lambda doc: doc.priority, reverse=True))
