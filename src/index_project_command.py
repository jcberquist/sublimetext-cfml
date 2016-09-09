import sublime_plugin
from .model_index import resync_project as index_project_cfcs
from .custom_tags import resync_project as index_project_custom_tags
from . import utils


class CfmlIndexProjectCommand(sublime_plugin.WindowCommand):

    def run(self):
        project_name = utils.get_project_name_from_window(self.window)
        if project_name:
            index_project_custom_tags(project_name)
            index_project_cfcs(project_name)
