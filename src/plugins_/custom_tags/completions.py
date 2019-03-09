from ...custom_tag_index import custom_tag_index
from ... import utils


def get_completions(cfml_view):
    if cfml_view.type == "tag":
        return get_tags(cfml_view)
    elif cfml_view.type == "tag_attributes":
        return get_tag_attributes(cfml_view)
    return None


def get_tags(cfml_view):
    if cfml_view.previous_char == "<":
        completion_list = custom_tag_index.get_prefix_completions(
            cfml_view.project_name
        )
        if completion_list:
            return cfml_view.CompletionList(completion_list, 0, False)
    elif cfml_view.previous_char == ":":
        prefix = cfml_view.view.substr(cfml_view.view.word(cfml_view.prefix_start - 1))
        completion_list = custom_tag_index.get_tag_completions(
            cfml_view.project_name, prefix
        )
        if completion_list:
            return cfml_view.CompletionList(completion_list, 0, False)
    return None


def get_tag_attributes(cfml_view):
    if not cfml_view.tag_name:
        return None

    if cfml_view.project_name in custom_tag_index.data:
        if ":" in cfml_view.tag_name or cfml_view.tag_name.lower().startswith("cf_"):
            completion_list = custom_tag_index.get_tag_attribute_completions(
                cfml_view.project_name, cfml_view.tag_name
            )
            if completion_list:
                return cfml_view.CompletionList(completion_list, 0, False)
    return None


def get_goto_cfml_file(cfml_view):
    if not cfml_view.project_name:
        return None

    if cfml_view.view.match_selector(cfml_view.position, "meta.tag.custom.cfml"):
        tag_name = utils.get_tag_name(cfml_view.view, cfml_view.position)

        file_path, tag_info = custom_tag_index.get_index_by_tag_name(
            cfml_view.project_name, tag_name
        )
        if file_path:
            return cfml_view.GotoCfmlFile(file_path, None)

    return None
