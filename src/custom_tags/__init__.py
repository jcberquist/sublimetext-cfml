from .. import completions, inline_documentation, goto_cfml_file, utils
from .custom_tags import CustomTags
from .documentation import get_documentation


custom_tags = CustomTags()


def get_completions(cfml_view):
    if cfml_view.type == 'tag':
        return get_tags(cfml_view)
    elif cfml_view.type == 'tag_attributes':
        return get_tag_attributes(cfml_view)
    return None


def get_tags(cfml_view):
    if cfml_view.previous_char == "<":
        completion_list = custom_tags.get_prefix_completions(cfml_view.project_name)
        if completion_list:
            return cfml_view.CompletionList(completion_list, 0, False)
    elif cfml_view.previous_char == ":":
        prefix = cfml_view.view.substr(cfml_view.view.word(cfml_view.prefix_start - 1))
        completion_list = custom_tags.get_tag_completions(cfml_view.project_name, prefix)
        if completion_list:
            return cfml_view.CompletionList(completion_list, 0, False)
    return None


def get_tag_attributes(cfml_view):
    if not cfml_view.tag_name:
        return None

    if cfml_view.project_name in custom_tags.data:
        if ":" in cfml_view.tag_name or cfml_view.tag_name.lower().startswith("cf_"):
            completion_list = custom_tags.get_tag_attribute_completions(cfml_view.project_name, cfml_view.tag_name)
            if completion_list:
                return cfml_view.CompletionList(completion_list, 0, False)
    return None


def get_inline_documentation(cfml_view, doc_type):
    if not cfml_view.project_name:
        return None

    if cfml_view.view.match_selector(cfml_view.position, 'meta.tag.custom.cfml'):
        tag_name = utils.get_tag_name(cfml_view.view, cfml_view.position)

        file_path, tag_info = custom_tags.get_index_by_tag_name(cfml_view.project_name, tag_name)
        if (file_path):
            doc, callback = get_documentation(cfml_view.view, tag_name, file_path, tag_info)
            return cfml_view.Documentation(None, doc, callback, 2)

    return None


def get_goto_cfml_file(cfml_view):
    if not cfml_view.project_name:
        return None

    if cfml_view.view.match_selector(cfml_view.position, 'meta.tag.custom.cfml'):
        tag_name = utils.get_tag_name(cfml_view.view, cfml_view.position)

        file_path, tag_info = custom_tags.get_index_by_tag_name(cfml_view.project_name, tag_name)
        if (file_path):
            return cfml_view.GotoCfmlFile(file_path, None)

    return None


def _plugin_loaded():
    custom_tags.sync_projects()
    completions.add_completion_source(get_completions)
    inline_documentation.add_documentation_source(get_inline_documentation)
    goto_cfml_file.add_goto_source(get_goto_cfml_file)
    utils.get_closing_custom_tags = custom_tags.get_closing_custom_tags
