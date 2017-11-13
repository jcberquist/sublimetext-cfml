import sublime
import sublime_plugin
from .. import utils


class CfmlNavigateToMethodCommand(sublime_plugin.WindowCommand):

    def run(self, file_path, href):

        if len(file_path) > 0:
            index_locations = self.window.lookup_symbol_in_index(href)

            for full_path, project_path, rowcol in index_locations:
                if utils.format_lookup_file_path(full_path) == file_path:
                    row, col = rowcol
                    self.window.open_file(full_path + ":" + str(row) + ":" + str(col), sublime.ENCODED_POSITION | sublime.FORCE_GROUP)
                    break
            else:
                # might be a setter, so for now just open the file
                self.window.open_file(file_path)
        else:
            # this symbol should be in active view
            view = self.window.active_view()
            functions = view.find_by_selector("meta.function.declaration.cfml entity.name.function.cfml")
            for funct_region in functions:
                if view.substr(funct_region).lower() == href.lower():
                    view.sel().clear()
                    r = sublime.Region(funct_region.begin())
                    view.sel().add(r)
                    view.show(r)
                    break
