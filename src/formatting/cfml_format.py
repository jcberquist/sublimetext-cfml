import sublime
import sublime_plugin
import time
from .. import utils
from . import blocks
from . import delimited_scopes
from . import alignment
from . import keywords
from . import method_chains
from . import misc
from . import whitespace


class CfmlFormatCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return self.view.match_selector(0, "embedding.cfml")

    def run(self, edit, current_method=True, settings=None):
        start_time = time.perf_counter()
        timing = []
        self.tab_size, self.translate_tabs_to_spaces, self.indent_str = (
            self.indent_settings()
        )
        self.region_to_format, self.has_sel = self.get_region_to_format(current_method)

        if self.region_to_format is None:
            return

        self.settings = {
            "inline_settings": {},
            "project_settings": {},
            "base_settings": sublime.load_settings("cfml_format.sublime-settings"),
        }
        if settings:
            self.settings["inline_settings"] = settings
        if (
            self.view.window().project_file_name()
            and "cfml_format" in self.view.window().project_data()
        ):
            self.settings["project_settings"] = (
                self.view.window().project_data().get("cfml_format")
            )

        self.region_updates(edit, whitespace.format_whitespace(self))
        timing.append(("whitespace", time.perf_counter()))

        self.region_updates(edit, keywords.format_keywords(self))
        timing.append(("keywords", time.perf_counter()))

        self.region_updates(edit, blocks.format_blocks(self))
        timing.append(("blocks", time.perf_counter()))

        self.region_updates(edit, delimited_scopes.format_delimited_scopes(self))
        timing.append(("delimited_scopes", time.perf_counter()))

        self.region_updates(edit, method_chains.format_method_chains(self))
        timing.append(("method_chains", time.perf_counter()))

        self.region_updates(edit, misc.normalize_strings(self))
        timing.append(("normalize_strings", time.perf_counter()))

        self.region_updates(edit, misc.normalize_builtin_functions(self))
        timing.append(("normalize_builtin_functions", time.perf_counter()))

        self.region_updates(edit, misc.format_properties(self))
        timing.append(("format_properties", time.perf_counter()))

        self.region_updates(edit, alignment.indent_region(self))
        self.region_updates(edit, alignment.align_assignment_operators(self))
        timing.append(("alignment", time.perf_counter()))

        if self.has_sel:
            self.view.sel().clear()
            self.view.sel().add(self.region_to_format)

        total_time = (
            "CFML format completed in "
            + "{:.0f}".format((time.perf_counter() - start_time) * 1000)
            + "ms"
        )

        if self.get_setting("log_command_times", default=False):
            last_tick = start_time
            for cmd, tick in timing:
                print(
                    "CFML format: {} completed in {:.0f}ms".format(
                        cmd, (tick - last_tick) * 1000
                    )
                )
                last_tick = tick

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
            cfc_selector = "source.cfml meta.class"
            funct_selector = "source.cfml meta.class meta.function"

            if self.view.match_selector(pt, funct_selector):
                for function_region in self.view.find_by_selector(funct_selector):
                    if function_region.contains(pt):
                        return function_region, False

            if self.view.match_selector(pt, cfc_selector):
                return None, False

        return sublime.Region(0, self.view.size()), False

    def get_setting(self, setting_key, sub_key=None, default=None):
        def search_settings(k, d=None):
            for t in ["inline_settings", "project_settings"]:
                if k in self.settings[t]:
                    return self.settings[t][k]
            return self.settings["base_settings"].get(k, d)

        if sub_key is not None:
            setting_key_parts = setting_key.split(".")
            full_key = ".".join(
                setting_key_parts[:1] + [sub_key] + setting_key_parts[1:]
            )
            setting = search_settings(full_key)
            if setting is not None:
                return setting

        return search_settings(setting_key, default)

    def region_updates(self, edit, updates):
        strs = []
        end_pt = self.view.size()

        for region, replacement_str in sorted(
            updates, reverse=True, key=lambda x: x[0]
        ):
            if self.region_to_format.contains(region):
                strs.append(self.view.substr(sublime.Region(region.end(), end_pt)))
                strs.append(replacement_str)
                end_pt = region.begin()

        if end_pt > 0:
            strs.append(self.view.substr(sublime.Region(0, end_pt)))

        full_src_text = "".join(reversed(strs))
        current_size = self.view.size()
        text_size_diff = len(full_src_text) - current_size
        slice_start, slice_end = (
            self.region_to_format.begin(),
            self.region_to_format.end() + text_size_diff,
        )
        replacement_txt = full_src_text[slice_start:slice_end]
        self.view.replace(edit, self.region_to_format, replacement_txt)
        text_size_diff = self.view.size() - current_size
        self.region_to_format = sublime.Region(
            self.region_to_format.begin(), self.region_to_format.end() + text_size_diff
        )

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
            nested_regions = self.view.find_by_selector(" ".join([selector] * depth))
            if len(nested_regions) == 0:
                break
            regions.extend(nested_regions)
            depth += 1

        regions.sort()
        return [r for r in regions if self.region_to_format.contains(r)]

    def inner_scope_spacing(
        self, region, empty_spacing, padding_inside, strip_newlines=False
    ):
        substitutions = []
        first_group_char = utils.get_next_character(self.view, region.begin() + 1)
        last_group_char = utils.get_previous_character(self.view, region.end() - 1)

        # is this region empty
        if first_group_char == region.end() - 1:
            if empty_spacing:
                replacement_region = sublime.Region(
                    region.begin() + 1, region.end() - 1
                )
                source_str = self.view.substr(replacement_region)
                if empty_spacing == "compact" and (
                    strip_newlines or "\n" not in source_str
                ):
                    substitutions.append((replacement_region, ""))
                elif empty_spacing == "spaced" and (
                    strip_newlines or "\n" not in source_str
                ):
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
