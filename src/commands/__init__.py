import sublime_plugin
from .. import utils
from ..component_index import component_index
from ..custom_tag_index import custom_tag_index
from .cfc_dotted_path import CfmlCfcDottedPathCommand, CfmlSidebarCfcDottedPathCommand
from .controller_view_toggle import CfmlToggleControllerViewCommand
from .color_scheme_styles import CfmlColorSchemeStylesCommand


class CloseCfmlTagCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            pt = sel.begin()
            cfml_only = self.view.match_selector(pt, "string")
            last_open_tag = utils.get_last_open_tag(
                self.view, pt - 1, cfml_only, custom_tag_index
            )
            if last_open_tag:
                if len(self.view.sel()) == 1:
                    self.view.run_command(
                        "insert", {"characters": "/" + last_open_tag + ">"}
                    )
                else:
                    self.view.insert(edit, pt, "/" + last_open_tag + ">")
            else:
                # if there is no open tag print "/"
                self.view.insert(edit, pt, "/")


class CfmlAutoInsertClosingTagCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pt = self.view.sel()[0].begin()
        if utils.get_setting("cfml_auto_insert_closing_tag"):
            tag_name = utils.get_tag_name(self.view, pt)
            if tag_name:
                is_custom_tag = self.view.match_selector(pt, "meta.tag.custom.cfml")
                if is_custom_tag:
                    closing_custom_tags = custom_tag_index.get_closing_custom_tags(
                        utils.get_project_name(self.view)
                    )
                    has_closing_tag = tag_name in closing_custom_tags
                else:
                    cfml_non_closing_tags = utils.get_setting("cfml_non_closing_tags")
                    has_closing_tag = tag_name not in cfml_non_closing_tags
                if has_closing_tag:
                    next_char = utils.get_next_character(self.view, pt)
                    tag_close_search_region = self.view.find("</" + tag_name + ">", pt)
                    if next_char != tag_close_search_region.begin():
                        self.view.run_command(
                            "insert_snippet", {"contents": ">$0</" + tag_name + ">"}
                        )
                        return
        self.view.run_command("insert_snippet", {"contents": ">"})


class CfmlBetweenTagPairCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pt = self.view.sel()[0].begin()
        cfml_between_tag_pair = utils.get_setting("cfml_between_tag_pair")
        if cfml_between_tag_pair in [
            "newline",
            "indent",
        ] and utils.between_cfml_tag_pair(self.view, pt):
            self.view.run_command(
                "insert_snippet",
                {
                    "contents": "\n"
                    + ("\t" if cfml_between_tag_pair == "indent" else "")
                    + "$0\n"
                },
            )
            return
        self.view.run_command("insert_snippet", {"contents": "\n"})


class CfmlEditSettingsCommand(sublime_plugin.WindowCommand):
    def run(self, file, default):
        package_file = file.replace("{cfml_package_name}", __name__.split(".")[0])
        self.window.run_command(
            "edit_settings", {"base_file": package_file, "default": default}
        )


class CfmlIndexProjectCommand(sublime_plugin.WindowCommand):
    def run(self):
        project_name = utils.get_project_name_from_window(self.window)
        if project_name:
            custom_tag_index.resync_project(project_name)
            component_index.resync_project(project_name)
