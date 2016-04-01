import sublime, sublime_plugin, webbrowser
from . import utils
from collections import namedtuple

Documentation = namedtuple('Documentation', 'doc_html_variables on_navigate priority')

DOC_TEMPLATE = ""
PAGINATION_TEMPLATE = ""

documentation_sources = []

def add_documentation_source(callback):
	documentation_sources.append(callback)

def get_inline_documentation(view, position):
	docs = [ ]

	for callback in documentation_sources:
		inline_doc = callback(view, position)
		if inline_doc:
			docs.append(inline_doc)

	return docs

def plugin_loaded():
	global DOC_TEMPLATE, PAGINATION_TEMPLATE
	DOC_TEMPLATE = sublime.load_resource("Packages/" + utils.get_plugin_name() + "/templates/inline_documentation.html").replace("\r", "")
	PAGINATION_TEMPLATE = sublime.load_resource("Packages/" + utils.get_plugin_name() + "/templates/pagination.html").replace("\r", "")

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

def build_doc_html(inline_doc):
	return sublime.expand_variables(DOC_TEMPLATE, inline_doc)

def get_on_navigate(view, docs, current_index):
	def on_navigate(href):
		if href.startswith("page_"):
			new_index = int(href.split("_").pop())
			display_documentation(view, docs, new_index)
		elif docs[current_index].on_navigate:
			docs[current_index].on_navigate(href)
		else:
			webbrowser.open_new_tab(href)
	return on_navigate

def generate_documentation(docs, current_index):
	doc_html_variables = dict(docs[current_index].doc_html_variables)
	doc_html_variables["pagination"] = build_pagination(current_index, len(docs)) if len(docs) > 1 else ""
	doc_html_variables["links"] = build_links(doc_html_variables["links"]) if "links" in doc_html_variables else ""

	return build_doc_html(doc_html_variables)

def display_documentation(view, docs, current_index=0):
	doc_html = generate_documentation(docs, current_index)
	on_navigate = get_on_navigate(view, docs, current_index)
	view.show_popup(doc_html, max_width=1024, max_height=480, on_navigate=on_navigate)

class CfmlInlineDocumentationCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		position = self.view.sel()[0].begin()
		docs = get_inline_documentation(self.view, position)
		if len(docs) > 0:
			display_documentation(self.view, sorted(docs, key=lambda doc: doc.priority, reverse=True))
