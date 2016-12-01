import sublime_plugin
from . import inline_documentation
from . import utils
from .cfml_view import CfmlView

completion_sources = []
completion_doc_sources = []


def add_completion_source(callback):
    completion_sources.append(callback)


def add_completion_doc_source(callback):
    completion_doc_sources.append(callback)


def get_completions(view, position, prefix):
    cfml_view = CfmlView(view, position, prefix)
    if not cfml_view.type:
        return None

    completion_lists = []
    minimum_priority = 0
    docs = []

    for callback in completion_sources:
        completionlist = callback(cfml_view)
        if completionlist:
            completion_lists.append(completionlist)
            if completionlist.exclude_lower_priority:
                minimum_priority = completionlist.priority

    if utils.get_setting("cfml_completion_docs"):
        for callback in completion_doc_sources:
            inline_doc = callback(cfml_view)
            if inline_doc:
                docs.append(inline_doc)

    full_completion_list = []
    for completionlist in sorted(completion_lists, key=lambda comp_list: comp_list.priority, reverse=True):
        if completionlist.priority >= minimum_priority:
            full_completion_list.extend(completionlist.completions)

    if len(docs) > 0:
        inline_documentation.display_documentation(view, docs, "completion_doc", 0)
    return full_completion_list


class CfmlUpdateCompletionDocCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.view.run_command("insert_snippet", {"contents": ","})
        if inline_documentation.doc_window == "completion_doc":
            position = self.view.sel()[0].begin()
            cfml_view = CfmlView(self.view, position)
            docs = []
            for callback in completion_doc_sources:
                inline_doc = callback(cfml_view)
                if inline_doc:
                    docs.append(inline_doc)

            if len(docs) > 0:
                inline_documentation.display_documentation(self.view, docs, "completion_doc", 0)
            else:
                self.view.hide_popup()
