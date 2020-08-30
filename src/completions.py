import sublime_plugin
from . import inline_documentation
from . import utils
from . import cfml_plugins
from .cfml_view import CfmlView


def get_completions(view, position, prefix):
    cfml_view = CfmlView(view, position, prefix)
    if not cfml_view.type:
        return None

    completion_lists = []
    minimum_priority = 0
    docs = []

    for p in cfml_plugins.plugins:
        completionlist = p.get_completions(cfml_view)
        if completionlist:
            completion_lists.append(completionlist)
            if completionlist.exclude_lower_priority:
                minimum_priority = completionlist.priority

    if utils.get_setting("cfml_completion_docs"):
        for p in cfml_plugins.plugins:
            inline_doc = p.get_completion_docs(cfml_view)
            if inline_doc:
                docs.append(inline_doc)

    full_completion_list = []
    for completionlist in completion_lists:
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
            for p in cfml_plugins.plugins:
                inline_doc = p.get_completion_docs(cfml_view)
                if inline_doc:
                    docs.append(inline_doc)

            if len(docs) > 0:
                inline_documentation.display_documentation(
                    self.view, docs, "completion_doc", 0
                )
            else:
                self.view.hide_popup()
