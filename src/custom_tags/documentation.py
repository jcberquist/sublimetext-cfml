from functools import partial
from .. import utils
from .custom_tags import get_index_by_tag_name

STYLES = {
    "side_color": "#934CB0",
    "header_color": "#352F38",
    "header_bg_color": "#EDE4F1",
    "text_color": "#352F38"
}


def get_inline_documentation(cfml_view):
    if not cfml_view.project_name:
        return None

    if cfml_view.view.match_selector(cfml_view.position, "meta.tag.custom.cfml"):
        tag_name = utils.get_tag_name(cfml_view.view, cfml_view.position)

        file_path, tag_info = get_index_by_tag_name(cfml_view.project_name, tag_name)
        if (file_path):
            doc, callback = get_documentation(cfml_view.view, tag_name, file_path, tag_info)
            return cfml_view.Documentation(doc, callback, 2)

    return None


def get_goto_cfml_file(cfml_view):
    if not cfml_view.project_name:
        return None

    if cfml_view.view.match_selector(cfml_view.position, "meta.tag.custom.cfml"):
        tag_name = utils.get_tag_name(cfml_view.view, cfml_view.position)

        file_path, tag_info = get_index_by_tag_name(cfml_view.project_name, tag_name)
        if (file_path):
            return cfml_view.GotoCfmlFile(file_path, None)

    return None


def on_navigate(view, file_path, href):
    view.window().open_file(file_path)


def get_documentation(view, tag_name, file_path, tag_info):
    custom_tag_doc = dict(STYLES)
    custom_tag_doc["links"] = []

    custom_tag_doc["header"] = tag_name
    custom_tag_doc["description"] = "<strong>path</strong>: <a class=\"alt-link\" href=\"__go_to_customtag\">" + file_path + "</a>"

    custom_tag_doc["body"] = "<br>"
    custom_tag_doc["body"] += "<strong>Closing tag:</strong> " + ("true" if tag_info["has_end_tag"] else "false") + "<br>"
    custom_tag_doc["body"] += "<strong>Attributes:</strong> " + ", ".join(tag_info["attributes"])

    callback = partial(on_navigate, view, file_path)
    return custom_tag_doc, callback
