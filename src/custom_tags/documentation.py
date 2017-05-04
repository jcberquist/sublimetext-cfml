from functools import partial
from .. import utils
from .custom_tags import get_index_by_tag_name

STYLES = {
    "side_color": "#934CB0",
    "link_color": "#306B7B",
    "header_bg_color": "#EDE4F1",
    "header_color": "#352F38",
    "paragraph_color": "#352F38"
}

ADAPTIVE_STYLES = {
    "side_color": "color(var(--orangish) blend(var(--background) 60%))",
    "link_color": "color(var(--orangish) blend(var(--foreground) 45%))",
    "header_bg_color": "color(var(--orangish) blend(var(--background) 60%))",
    "header_color": "color(var(--foreground) blend(var(--orangish) 95%))"
}


def get_inline_documentation(cfml_view, doc_type):
    if not cfml_view.project_name:
        return None

    if cfml_view.view.match_selector(cfml_view.position, "meta.tag.custom.cfml"):
        tag_name = utils.get_tag_name(cfml_view.view, cfml_view.position)

        file_path, tag_info = get_index_by_tag_name(cfml_view.project_name, tag_name)
        if (file_path):
            doc, callback = get_documentation(cfml_view.view, tag_name, file_path, tag_info)
            return cfml_view.Documentation(None, doc, callback, 2)

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
    custom_tag_doc = {"styles": STYLES, "adaptive_styles": ADAPTIVE_STYLES, "html": {}}
    custom_tag_doc["html"]["links"] = []

    custom_tag_doc["html"]["header"] = tag_name
    custom_tag_doc["html"]["description"] = "<strong>path</strong>: <a class=\"plain-link\" href=\"__go_to_customtag\">" + file_path + "</a>"

    custom_tag_doc["html"]["body"] = "<br>"
    custom_tag_doc["html"]["body"] += "<strong>Closing tag:</strong> " + ("true" if tag_info["has_end_tag"] else "false") + "<br>"
    custom_tag_doc["html"]["body"] += "<strong>Attributes:</strong> " + ", ".join(tag_info["attributes"])

    callback = partial(on_navigate, view, file_path)
    return custom_tag_doc, callback
