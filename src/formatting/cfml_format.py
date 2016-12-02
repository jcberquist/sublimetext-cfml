import sublime
import sublime_plugin
import time
from .. import utils
from . import blocks
from . import delimited_scopes
from . import keywords
from . import method_chains
from . import whitespace
from . import misc

COMMANDS = [
    {"name": "whitespace", "label": "Format Whitespace"},
    {"name": "keywords", "label": "Format Keywords"},
    {"name": "blocks", "label": "Format Blocks"},
    {"name": "delimited_scopes", "label": "Format Delimited Scopes"},
    {"name": "method_chains", "label": "Format Method Chains"},
    {"name": "normalize_strings", "label": "Normalize Strings"},
    {"name": "normalize_builtin_functions", "label": "Normalize Built-in Functions"},
    {"name": "format_properties", "label": "Format Properties"}
]


class CfmlFormatMenuCommand(sublime_plugin.TextCommand):

    def run(self, edit):

        self.commands = []
        if self.view.match_selector(self.view.sel()[0].a, "source.cfml.script meta.class"):
            self.commands.append({"name": "full_component", "label": ["Full Component Format - Uses Default Command Array"]})
            if self.view.match_selector(self.view.sel()[0].a, "source.cfml.script meta.class meta.function"):
                self.commands.append({"name": "current_function", "label": "Current Method Format - Uses Default Command Array"})
        else:
            self.commands.append({"name": "cfscript", "label": "Format CFScript - Uses Default Command Array"})

        self.commands.extend(COMMANDS)
        menu = [c["label"] for c in self.commands]

        self.view.window().show_quick_panel(menu, self.run_command)

    def run_command(self, index):
        if index < 0:
            return
        if self.commands[index]["name"] in ["full_component", "cfscript"]:
            self.view.run_command("cfml_format", {"commands": [], "current_method": False})
        elif self.commands[index]["name"] == "current_function":
            self.view.run_command("cfml_format", {"commands": [], "current_method": True})
        else:
            self.view.run_command("cfml_format", {"commands": [self.commands[index]["name"]], "current_method": False})


class CfmlFormatCommand(sublime_plugin.TextCommand):

    def run(self, edit, commands=[], current_method=True, settings=None):
        start_time = time.time()
        timing = []
        self.tab_size, self.translate_tabs_to_spaces, self.indent_str = self.indent_settings()
        self.region_to_format, self.has_sel = self.get_region_to_format(current_method)

        if self.region_to_format is None:
            return

        if settings:
            self.settings = settings
        elif self.view.window().project_file_name() and "cfml_format" in self.view.window().project_data():
            self.settings = self.view.window().project_data().get("cfml_format")
        else:
            self.settings = sublime.load_settings("cfml_format.sublime-settings")

        self.commands = commands if len(commands) > 0 else self.get_setting("default_commands")

        if "whitespace" in self.commands:
            tick = time.time()
            delimited_scope_command = "delimited_scopes" in self.commands
            self.region_updates(edit, whitespace.format_whitespace(self, delimited_scope_command))
            timing.append(('whitespace', time.time() - tick))
        if "keywords" in self.commands:
            tick = time.time()
            self.region_updates(edit, keywords.format_keywords(self))
            timing.append(('keywords', time.time() - tick))
        if "blocks" in self.commands:
            tick = time.time()
            self.region_updates(edit, blocks.format_blocks(self))
            timing.append(('blocks', time.time() - tick))
        if "delimited_scopes" in self.commands:
            tick = time.time()
            self.region_updates(edit, delimited_scopes.format_delimited_scopes(self))
            timing.append(('delimited_scopes', time.time() - tick))
        if "method_chains" in self.commands:
            tick = time.time()
            self.region_updates(edit, method_chains.format_method_chains(self))
            timing.append(('method_chains', time.time() - tick))
        if "normalize_strings" in self.commands:
            tick = time.time()
            self.region_updates(edit, misc.normalize_strings(self))
            timing.append(('normalize_strings', time.time() - tick))
        if "normalize_builtin_functions" in self.commands:
            tick = time.time()
            self.region_updates(edit, misc.normalize_builtin_functions(self))
            timing.append(('normalize_builtin_functions', time.time() - tick))
        if "format_properties" in self.commands:
            tick = time.time()
            self.region_updates(edit, misc.format_properties(self))
            timing.append(('format_properties', time.time() - tick))

        if self.has_sel:
            self.view.sel().clear()
            self.view.sel().add(self.region_to_format)

        total_time = "CFML format completed in " + "{:.0f}".format((time.time() - start_time) * 1000) + "ms"

        if (self.get_setting("log_command_times", default=False)):
            for cmd, diff in timing:
                print("CFML format: '" + cmd + "' completed in " + "{:.0f}".format(diff * 1000) + "ms")
        print(total_time)
        sublime.status_message(total_time)

    def indent_settings(self):
        """
        indent settings for the view
        """
        tab_size = self.view.settings().get("tab_size")
        translate_tabs_to_spaces = self.view.settings().get("translate_tabs_to_spaces")
        indent_str = " " * tab_size if translate_tabs_to_spaces else "\t"
        return tab_size, translate_tabs_to_spaces, indent_str

    def get_region_to_format(self, current_method):
        if self.view.sel()[0].size() > 0:
            return self.view.sel()[0], True
        if current_method:
            pt = self.view.sel()[0].begin()
            cfc_selector = "source.cfml.script meta.class"
            decl_selector = "source.cfml.script meta.class.body.cfml meta.function.declaration.cfml"
            body_selector = "source.cfml.script meta.class.body.cfml meta.function.body.cfml"

            in_cfc = self.view.match_selector(pt, cfc_selector)
            in_funct_decl = self.view.match_selector(pt, decl_selector)
            in_funct_body = self.view.match_selector(pt, body_selector)

            if in_funct_decl or in_funct_body:
                if in_funct_body:
                    funct_body_region = utils.get_scope_region_containing_point(self.view, pt, body_selector)
                    funct_decl_pt = funct_body_region.begin() - 1
                    funct_decl_region = utils.get_scope_region_containing_point(self.view, funct_decl_pt, decl_selector)
                else:
                    funct_decl_region = utils.get_scope_region_containing_point(self.view, pt, decl_selector)
                    funct_body_pt = funct_decl_region.end()
                    funct_body_region = utils.get_scope_region_containing_point(self.view, funct_body_pt, body_selector)

                function_region = sublime.Region(funct_decl_region.begin(), funct_body_region.end())
                return function_region, False
            if in_cfc:
                return None, False

        return sublime.Region(0, self.view.size()), False

    def get_setting(self, setting_key, sub_key=None, default=None):
        if sub_key is not None:
            setting = self.settings.get(setting_key + "-" + sub_key)
            if setting is not None:
                return setting

        return self.settings.get(setting_key, default)

    def region_updates(self, edit, updates):

        def full_text_replace(full_text, region, replacement_str):
            updated_text = ""
            if region.begin() > 0:
                updated_text += full_text[:region.begin()]
            updated_text += replacement_str
            if region.end() < len(full_text):
                updated_text += full_text[region.end():]
            return updated_text

        full_region = sublime.Region(0, self.view.size())
        old_src_text = full_src_text = self.view.substr(full_region)

        for region, replacement_str in sorted(updates, reverse=True, key=lambda x: x[0]):
            if self.region_to_format.contains(region):
                full_src_text = full_text_replace(full_src_text, region, replacement_str)

        text_size_diff = len(full_src_text) - len(old_src_text)
        replacement_txt = full_src_text[self.region_to_format.begin():(self.region_to_format.end() + text_size_diff)]

        self.view.replace(edit, self.region_to_format, replacement_txt)
        self.region_to_format = sublime.Region(self.region_to_format.begin(), self.region_to_format.end() + text_size_diff)

    def text_columns(self, text):
        """
        returns the computed columns in the given source text
        """
        tab_count = text.count("\t")
        newline_count = text.count("\n")
        return len(text) - tab_count - newline_count + (self.tab_size * tab_count)

    def text_indent_columns(self, text):
        """
        returns the computed text column of the first non whitespace character in the text
        """
        whitespace_size = len(text) - len(text.lstrip())
        return self.text_columns(text[:whitespace_size])

    def region_columns(self, region):
        """
        returns the computed columns in the given region
        """
        region_text = self.view.substr(region)
        return self.text_columns(region_text)

    def pt_column(self, pt):
        """
        returns the computed line column of the given point
        """
        start_of_line = sublime.Region(self.view.line(pt).begin(), pt)
        return self.region_columns(start_of_line) + 1

    def line_indent_column(self, pt):
        """
        returns the computed line column of the first non whitespace character on the line of the given point
        """
        line = self.view.line(pt)
        next_char_pt = utils.get_next_character(self.view, line.begin())
        indent_region = sublime.Region(line.begin(), next_char_pt)
        return self.region_columns(indent_region)

    def region_end_col(self, region):
        """
        computes the last column of a region by adding its internal column size
        to the column length of the first point of the region
        """
        return self.pt_column(region.begin()) + self.region_columns(region)

    def indent_to_column(self, column):
        """
        returns a string padded to the specified column
        """
        result = self.indent_str * int(column / self.tab_size)
        result += " " * (column % self.tab_size)
        return result

    def find_by_selector(self, selector):
        regions = self.view.find_by_selector(selector)
        return [r for r in regions if self.region_to_format.contains(r)]

    def find_by_nested_selector(self, selector):
        depth = 1
        regions = []
        while True:
            nested_regions = self.find_by_selector(" ".join([selector] * depth))
            if len(nested_regions) == 0:
                regions.sort()
                return regions
            regions.extend(nested_regions)
            depth += 1

    def inner_scope_spacing(self, region, empty_spacing, padding_inside, strip_newlines=False):
        substitutions = []
        first_group_char = utils.get_next_character(self.view, region.begin() + 1)
        last_group_char = utils.get_previous_character(self.view, region.end() - 1)

        # is this region empty
        if first_group_char == region.end() - 1:
            if empty_spacing:
                replacement_region = sublime.Region(region.begin() + 1, region.end() - 1)
                source_str = self.view.substr(replacement_region)
                if empty_spacing == "compact" and (strip_newlines or "\n" not in source_str):
                    substitutions.append((replacement_region, ""))
                elif empty_spacing == "spaced" and (strip_newlines or "\n" not in source_str):
                    substitutions.append((replacement_region, " "))

        elif padding_inside is not None:
            space_str = " " if padding_inside == "spaced" else ""

            start_to_char = sublime.Region(region.begin() + 1, first_group_char)
            start_to_char_str = self.view.substr(start_to_char)
            if strip_newlines or "\n" not in start_to_char_str:
                substitutions.append((start_to_char, space_str))

            char_to_end = sublime.Region(last_group_char + 1, region.end() - 1)
            char_to_end_str = self.view.substr(char_to_end)
            if strip_newlines or "\n" not in char_to_end_str:
                substitutions.append((char_to_end, space_str))

        return substitutions

    def is_full_scope(self, region, start_selector, end_selector):
        start_scope_name = self.view.scope_name(region.begin()).strip()
        end_scope_name = self.view.scope_name(region.end() - 1).strip()
        start_scope_parts = start_scope_name.split(" ")

        if start_scope_parts[-1] != start_selector:
            return False

        target_end_scope = " ".join(start_scope_parts[:-1]) + " " + end_selector
        if target_end_scope != end_scope_name:
            return False

        return True
