import sublime
import sublime_plugin
from os.path import dirname
from .. import utils


def cfc_files(files):
    return [
        file_path for file_path in files if file_path.split(".")[-1].lower() == "cfc"
    ]


def get_project_info(window):
    project_data = window.project_data()
    project_path = (
        dirname(window.project_file_name()) if window.project_file_name() else None
    )
    return project_data, project_path


def get_dotted_paths(window, file_path):
    dotted_paths = []
    normalized_path = utils.normalize_path(file_path)
    project_data, project_path = get_project_info(window)

    if "mappings" in project_data:
        for mapping in project_data["mappings"]:
            normalized_mapping = utils.normalize_mapping(mapping, project_path)
            if normalized_path.startswith(normalized_mapping["path"]):
                mapped_path = normalized_mapping["mapping"] + normalized_path.replace(
                    normalized_mapping["path"], ""
                )
                path_parts = mapped_path.split("/")[1:]
                dotted_paths.append(".".join(path_parts)[:-4])

    # fall back to folders if no mappings matched
    if len(dotted_paths) == 0:
        for folder in project_data["folders"]:
            relative_path = normalized_path.replace(
                utils.normalize_path(folder["path"], project_path), ""
            )
            if relative_path != normalized_path:
                path_parts = relative_path.split("/")[1:]
                dotted_paths.append(".".join(path_parts)[:-4])

    return dotted_paths


def copy_path(window, files):
    def on_done(i):
        if i != -1:
            sublime.set_clipboard(dotted_paths[i])
            sublime.status_message("CFML: copied cfc dotted path")

    dotted_paths = get_dotted_paths(window, cfc_files(files)[0])

    if len(dotted_paths) > 1:
        window.show_quick_panel(dotted_paths, on_done)
    else:
        on_done(0)


class CfmlCfcDottedPathCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if len(self.view.file_name()) > 0:
            copy_path(self.view.window(), [self.view.file_name()])

    def is_visible(self):
        return (
            self.view.file_name() is not None
            and len(cfc_files([self.view.file_name()])) == 1
        )


class CfmlSidebarCfcDottedPathCommand(sublime_plugin.WindowCommand):
    def run(self, files):
        copy_path(self.window, files)

    def is_visible(self, files):
        return len(cfc_files(files)) == 1
