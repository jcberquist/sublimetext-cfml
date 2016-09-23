import sublime
from . import utils
from . import inline_documentation
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

    for callback in completion_doc_sources:
        inline_doc = callback(cfml_view)
        if inline_doc:
            docs.append(inline_doc)

    full_completion_list = []
    for completionlist in sorted(completion_lists, key=lambda comp_list: comp_list.priority, reverse=True):
        if completionlist.priority >= minimum_priority:
            full_completion_list.extend(completionlist.completions)

    if len(docs) > 0:
        inline_documentation.display_documentation(view, docs, 0, True)
    return full_completion_list
