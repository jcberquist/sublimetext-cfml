import sublime_plugin
from functools import partial
from . import inline_documentation
from . import utils
from . import view_state
from . import cfml_providers
from .cfml_view import CfmlView


def get_completion_docs(cfml_view):
    docs = []
    for p in cfml_providers.providers:
        inline_doc = p.get_completion_docs(cfml_view)
        if inline_doc:
            docs.append(inline_doc)
    return sorted(docs, key=lambda doc: doc.priority, reverse=True)


def refresh_completion_docs(view, position, prefix):
    # a doc finished loading; show the docs again unless the caret has moved
    if not view.is_valid() or len(view.sel()) == 0:
        return
    if view.sel()[0].begin() != position:
        return
    docs = get_completion_docs(CfmlView(view, position, prefix))
    if len(docs) > 0:
        inline_documentation.display_documentation(view, docs, 'completion_doc', 0)


def get_completions(view, position, prefix):
    cfml_view = CfmlView(view, position, prefix)
    if not cfml_view.type:
        return None
    cfml_view.on_data_loaded = partial(refresh_completion_docs, view, position, prefix)

    completions = []
    docs = []

    for p in cfml_providers.providers:
        provider_completions = p.get_completions(cfml_view)
        if provider_completions:
            completions.extend(provider_completions)

    if utils.get_setting('cfml_completion_docs'):
        docs = get_completion_docs(cfml_view)

    if len(docs) > 0:
        inline_documentation.display_documentation(view, docs, 'completion_doc', 0)
    return completions


class CfmlUpdateCompletionDocCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command('insert_snippet', {'contents': ','})
        popup = view_state.get(self.view).doc_popup
        if popup and popup.doc_type == 'completion_doc':
            position = self.view.sel()[0].begin()
            cfml_view = CfmlView(self.view, position)
            cfml_view.on_data_loaded = partial(
                refresh_completion_docs, self.view, position, ''
            )
            docs = get_completion_docs(cfml_view)

            if len(docs) > 0:
                inline_documentation.display_documentation(
                    self.view, docs, 'completion_doc', 0
                )
            else:
                self.view.hide_popup()
