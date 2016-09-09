from . import utils
from .cfml_view import CfmlView

completion_sources = []


def add_completion_source(callback):
    completion_sources.append(callback)


def get_completions(view, position, prefix):
    cfml_view = CfmlView(view, position, prefix)
    if not cfml_view.type:
        return None

    completion_lists = []
    minimum_priority = 0

    for callback in completion_sources:
        completionlist = callback(cfml_view)
        if completionlist:
            completion_lists.append(completionlist)
            if completionlist.exclude_lower_priority:
                minimum_priority = completionlist.priority

    full_completion_list = []
    for completionlist in sorted(completion_lists, key=lambda comp_list: comp_list.priority, reverse=True):
        if completionlist.priority >= minimum_priority:
            full_completion_list.extend(completionlist.completions)

    return full_completion_list
