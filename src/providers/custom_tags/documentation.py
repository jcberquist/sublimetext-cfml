from functools import partial
from ...custom_tag_index import custom_tag_index
from ... import minihtml, utils
from ...cfml_view import Documentation
from ...project_watcher import project_watcher


# the color of the side of the docs, a hue of the color scheme
ACCENT: minihtml.Hue = "orangish"


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
                cfml_view.view,
                tag_name,
                file_path,
                tag_info,
                project_watcher.get_project_folders(cfml_view.project_name),
            )
            return Documentation(None, doc, callback, 2)

    return None


def get_documentation(view, tag_name, file_path, tag_info, folders):
    custom_tag_doc = minihtml.Doc(ACCENT, minihtml.escape_text(tag_name))
    custom_tag_doc.body = minihtml.path("__go_to_customtag", file_path, folders)
    custom_tag_doc.body += minihtml.card(
        minihtml.header(
            "closing tag",
            "true" if tag_info["has_end_tag"] else "false",
            "constant.language",
        )
    )
    if tag_info["attributes"]:
        custom_tag_doc.body += minihtml.card(
            minihtml.header(
                "attributes",
                ", ".join(tag_info["attributes"]),
                "entity.other.attribute-name",
            )
        )

    callback = partial(on_navigate, view, file_path)
    return custom_tag_doc, callback


def on_navigate(view, file_path, href):
    view.window().open_file(file_path)
