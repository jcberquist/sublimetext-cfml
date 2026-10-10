import sublime
import sublime_plugin
from .. import utils


class CfmlNavigateToMethodCommand(sublime_plugin.WindowCommand):
    def run(self, file_path, href):

        if len(file_path) > 0:
            location = utils.find_symbol_location(self.window, href, file_path)
            if location:
                self.window.open_file(
                    location.path_encoded_position(),
                    sublime.NewFileFlags.ENCODED_POSITION
                    | sublime.NewFileFlags.FORCE_GROUP,
                )
            else:
                # might be a setter, so for now just open the file
                self.window.open_file(file_path)
        else:
            # this symbol should be in active view
            view = self.window.active_view()
            if view is None:
                return
            # tag component functions have no meta.function.declaration scope
            functions = view.find_by_selector(
                'entity.name.function - meta.function.body'
            )
            for funct_region in functions:
                if view.substr(funct_region).lower() == href.lower():
                    view.sel().clear()
                    r = sublime.Region(funct_region.begin())
                    view.sel().add(r)
                    view.show(r)
                    break
