from .. import completions, inline_documentation, goto_cfml_file, utils
from .custom_tags import *
from .documentation import get_inline_documentation, get_goto_cfml_file


def plugin_loaded():
    custom_tags.sync_projects()
    completions.add_completion_source(get_completions)
    inline_documentation.add_documentation_source(get_inline_documentation)
    goto_cfml_file.add_goto_source(get_goto_cfml_file)
    utils.get_closing_custom_tags = get_closing_custom_tags


def get_completions(cfml_view):
    if cfml_view.type == 'tag':
        return get_tags(cfml_view)
    elif cfml_view.type == 'tag_attributes':
        return get_tag_attributes(cfml_view)
    return None


def get_tags(cfml_view):
    if cfml_view.previous_char == "<":
        completion_list = get_prefix_completions(cfml_view.project_name)
        if completion_list:
            return cfml_view.CompletionList(completion_list, 0, False)
    elif cfml_view.previous_char == ":":
        prefix = cfml_view.view.substr(cfml_view.view.word(cfml_view.prefix_start - 1))
        completion_list = get_tag_completions(cfml_view.project_name, prefix)
        if completion_list:
            return cfml_view.CompletionList(completion_list, 0, False)
    return None


def get_tag_attributes(cfml_view):
    if not cfml_view.tag_name:
        return None

    if cfml_view.project_name in custom_tags.projects:
        if ":" in cfml_view.tag_name or cfml_view.tag_name.lower().startswith("cf_"):
            completion_list = get_tag_attribute_completions(cfml_view.project_name, cfml_view.tag_name)
            if completion_list:
                return cfml_view.CompletionList(completion_list, 0, False)
    return None
