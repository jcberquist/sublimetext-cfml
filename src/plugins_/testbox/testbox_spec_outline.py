import sublime
import sublime_plugin
from ... import utils

testbox_function_names = [
    "describe",
    "it",
    "feature",
    "scenario",
    "story",
    "given",
    "when",
    "then",
]
func_call_scope = "meta.function-call.cfml variable.function.cfml"
string_scope = "meta.function-call.cfml meta.function-call.parameters.cfml meta.string"
func_param_name_scope = "meta.function-call.cfml meta.function-call.parameters.cfml entity.other.function-parameter.cfml"


class TestboxSpecOutlineCommand(sublime_plugin.TextCommand):
    def run(self, edit):

        # sanity check
        if not self.view.match_selector(0, "embedding.cfml"):
            return

        self.outline = []
        self.outline_regions = []
        self.selected_index = 0, None
        self.current_regions = [r for r in self.view.sel()]
        self.viewport_position = self.view.viewport_position()

        # collect title parameters
        title_params = {}
        for r in self.view.find_by_selector(func_param_name_scope):
            if self.view.substr(r).lower() == "title":
                title_params[r.begin()] = r

        # collect strings
        string_descriptions = {
            r.begin(): r for r in self.view.find_by_selector(string_scope)
        }

        # build outline
        for r in self.view.find_by_selector(func_call_scope):
            func_name = self.view.substr(r).lower()

            # continue if not a testbox func call
            if func_name not in testbox_function_names:
                continue

            # find the `(` after the func name
            next_pt = utils.get_next_character(self.view, r.end())

            # find the next pt - could be string start or named title param
            next_pt = utils.get_next_character(self.view, next_pt + 1)

            # check for named title param
            if next_pt in title_params:
                # get `=`
                next_pt = utils.get_next_character(
                    self.view, title_params[next_pt].end()
                )
                # look for title string
                next_pt = utils.get_next_character(self.view, next_pt + 1)

            if next_pt in string_descriptions:
                # looks like a something we care about
                string_region = string_descriptions[next_pt]
                depth = (
                    self.view.scope_name(r.begin()).count("meta.function.body.cfml") - 1
                )
                indent = "    " * depth
                self.outline.append(
                    indent + func_name + ": " + self.view.substr(string_region)[1:-1]
                )
                self.outline_regions.append(string_region)

                distance = self.distance(string_region)
                if self.selected_index[1] is None or distance < self.selected_index[1]:
                    self.selected_index = len(self.outline_regions) - 1, distance

        if len(self.outline) == 0:
            return

        self.view.window().show_quick_panel(
            self.outline,
            self.on_done,
            selected_index=self.selected_index[0],
            on_highlight=self.on_highlight,
        )

    def distance(self, region):
        pt = self.current_regions[0].begin()
        if region.contains(pt):
            return 0
        if pt < region.begin():
            return region.begin() - pt
        return pt - region.end()

    def refresh(self):
        # workaround the selection updates not being drawn
        self.view.add_regions("force_refresh", [])
        self.view.erase_regions("force_refresh")

    def on_done(self, i):
        if i == -1:
            # nothing selected, reset
            self.view.sel().clear()
            self.view.sel().add_all(self.current_regions)
            self.view.set_viewport_position(self.viewport_position)

    def on_highlight(self, i):
        self.view.sel().clear()
        self.view.sel().add(self.outline_regions[i])
        self.view.show_at_center(self.outline_regions[i])
        self.refresh()
