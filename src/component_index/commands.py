import sublime_plugin
from .. import utils
from ..project_watcher import project_watcher
from . import component_index


class CfmlIndexProjectCommand(sublime_plugin.WindowCommand):
    def run(self):
        project_name = utils.get_project_name_from_window(self.window)
        if project_name:
            project_watcher.resync_project(project_name)


class CfmlClearIndexCacheCommand(sublime_plugin.WindowCommand):
    def run(self):
        # the cache is shared by all projects, so all are indexed again
        component_index.clear_cache()
