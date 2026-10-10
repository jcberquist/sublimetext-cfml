import sublime
import sublime_plugin
from os.path import dirname
from .. import utils


def cfc_files(files):
    return [
        file_path for file_path in files if file_path.split('.')[-1].lower() == 'cfc'
    ]


def get_project_info(window):
    # a window without a project or folders has no project data
    project_data = window.project_data() or {}
    project_path = (
        dirname(window.project_file_name()) if window.project_file_name() else None
    )
    return project_data, project_path


def get_dotted_paths(window, file_path):
    dotted_paths = []
    normalized_path = utils.normalize_path(file_path)
    project_data, project_path = get_project_info(window)

    if 'mappings' in project_data:
        for mapping in project_data['mappings']:
            normalized_mapping = utils.normalize_mapping(mapping, project_path)
            path_parts = utils.get_mapped_path_parts(
                normalized_path, normalized_mapping
            )
            if path_parts:
                dotted_paths.append('.'.join(path_parts)[:-4])

    # fall back to folders if no mappings matched
    if len(dotted_paths) == 0:
        for folder in project_data.get('folders', []):
            folder_mapping = {
                'path': utils.normalize_path(folder['path'], project_path),
                'mapping': '',
            }
            path_parts = utils.get_mapped_path_parts(normalized_path, folder_mapping)
            if path_parts:
                dotted_paths.append('.'.join(path_parts)[:-4])

    return dotted_paths


def copy_path(window, files):
    def on_done(i):
        if i != -1:
            sublime.set_clipboard(dotted_paths[i])
            sublime.status_message('CFML: copied cfc dotted path')

    dotted_paths = get_dotted_paths(window, cfc_files(files)[0])

    if len(dotted_paths) == 0:
        sublime.status_message('CFML: the cfc is not in a project folder or mapping')
    elif len(dotted_paths) > 1:
        window.show_quick_panel(dotted_paths, on_done)
    else:
        on_done(0)


class CfmlCfcDottedPathCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_name = self.view.file_name()
        if file_name:
            copy_path(self.view.window(), [file_name])

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
