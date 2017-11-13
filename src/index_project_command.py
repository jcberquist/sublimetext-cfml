import sublime_plugin
from .component_index import component_index
from .custom_tags import custom_tags
from . import utils


class CfmlIndexProjectCommand(sublime_plugin.WindowCommand):

    def run(self):
        project_name = utils.get_project_name_from_window(self.window)
        if project_name:
            custom_tags.resync_project(project_name)
            component_index.resync_project(project_name)
