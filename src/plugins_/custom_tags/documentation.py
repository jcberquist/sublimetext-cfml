from functools import partial
from ...custom_tag_index import custom_tag_index
from ... import utils


SIDE_COLOR = "color(var(--orangish) blend(var(--background) 60%))"


def get_inline_documentation(cfml_view, doc_type):
    if not cfml_view.project_name:
        return None

    if cfml_view.view.match_selector(cfml_view.position, "meta.tag.custom.cfml"):
        tag_name = utils.get_tag_name(cfml_view.view, cfml_view.position)

        file_path, tag_info = custom_tag_index.get_index_by_tag_name(
            cfml_view.project_name, tag_name
        )
        if file_path:
            doc, callback = get_documentation(
                cfml_view.view, tag_name, file_path, tag_info
            )
            return cfml_view.Documentation(None, doc, callback, 2)

    return None


def get_documentation(view, tag_name, file_path, tag_info):
    custom_tag_doc = {"side_color": SIDE_COLOR, "html": {}}
    custom_tag_doc["html"]["links"] = []

    custom_tag_doc["html"]["header"] = tag_name
    custom_tag_doc["html"]["description"] = (
        '<strong>path</strong>: <a class="plain-link" href="__go_to_customtag">'
        + file_path
        + "</a>"
    )

    custom_tag_doc["html"]["body"] = "<br>"
    custom_tag_doc["html"]["body"] += (
        "<strong>Closing tag:</strong> "
        + ("true" if tag_info["has_end_tag"] else "false")
        + "<br>"
    )
    custom_tag_doc["html"]["body"] += "<strong>Attributes:</strong> " + ", ".join(
        tag_info["attributes"]
    )

    callback = partial(on_navigate, view, file_path)
    return custom_tag_doc, callback


def on_navigate(view, file_path, href):
    view.window().open_file(file_path)
