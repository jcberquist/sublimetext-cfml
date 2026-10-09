from functools import partial
from ... import component_reference
from ... import minihtml
from ...cfml_view import Documentation
from ...project_watcher import project_watcher


# the color of the side of the docs, a hue of the color scheme
ACCENT: minihtml.Hue = "bluish"


def get_inline_documentation(cfml_view, reference):
    documentation = component_reference.get_inline_documentation(cfml_view, reference)
    if documentation:
        return documentation

    # the component is not indexed, so there is only its path to show
    doc, callback = get_documentation(
        cfml_view.view,
        reference.file_path,
        minihtml.span_wrap(reference.class_name, "entity.name.class"),
        project_watcher.get_project_folders(cfml_view.project_name),
    )
    return Documentation(reference.regions, doc, callback, 2)


def on_navigate(view, file_path, href):
    view.window().open_file(file_path)


def get_documentation(view, file_path, header, folders):
    cfc_doc = minihtml.Doc(
        ACCENT, header, minihtml.path("__go_to_component", file_path, folders)
    )

    callback = partial(on_navigate, view, file_path)
    return cfc_doc, callback
