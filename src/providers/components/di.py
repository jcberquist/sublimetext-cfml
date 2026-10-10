import sublime
import sublime_plugin
from typing import Any
from . import cfcs, variable_names
from ... import utils
from ...cfml_view import CfmlView


def get_property_name(cfml_view, reference):
    """
    Returns the name of the property to add for a component found at the
    view's position, or None when what it was found by is already an
    injected property of the component: its bean or class is named
    differently, and is not a property to add.
    """
    # the name the component was found by is the last of the regions
    name = cfml_view.view.substr(reference.regions[-1])
    if variable_names.get_injected_property(cfml_view, name):
        return None
    return reference.class_name


class CfmlDiPropertyCommand(sublime_plugin.TextCommand):
    def run(self, edit, property_name=None):

        pt = self.view.sel()[0].begin()

        if not self.view.match_selector(pt, 'source.cfml meta.class'):
            return

        if property_name:
            self.insert_property(edit, property_name)
            return

        cfml_view = CfmlView(self.view, pt)

        if not cfml_view.project_name:
            return

        reference = variable_names.find_cfc(cfml_view)

        if reference:
            property_name = get_property_name(cfml_view, reference)
            if property_name:
                self.insert_property(edit, property_name)
        else:
            window = self.view.window()
            if window is None:
                return
            cfc_list = cfcs.get_cfc_list(cfml_view.project_name)

            def callback(i):
                if i > -1:
                    self.view.run_command(
                        'cfml_di_property', {'property_name': cfc_list[i]}
                    )

            window.show_quick_panel(
                cfc_list, callback, flags=sublime.QuickPanelFlags.MONOSPACE_FONT
            )

    def insert_property(self, edit, property_name):
        di_property = utils.get_project_setting(self.view.window(), 'di_property')
        is_script = (
            len(self.view.find_by_selector('source.cfml.script meta.class.body.cfml'))
            > 0
        )
        property_string = (
            di_property.get('script_template', '')
            if is_script
            else di_property.get('tag_template', '')
        )

        if '{name}' not in property_string:
            return

        properties = self.view.find_by_selector('meta.tag.property.cfml')
        property_names = [
            self.view.substr(r).lower()
            for r in self.view.find_by_selector('meta.tag.property.name.cfml')
        ]

        if property_name.lower() in property_names:
            return

        if len(properties) > 0:
            indent_region = sublime.Region(
                self.view.line(properties[-1]).begin(), properties[-1].begin()
            )
            indent_string = '\n' + self.view.substr(indent_region)
            injection_pt = properties[-1].end()
        else:
            tab_size: Any = self.view.settings().get('tab_size')
            translate_tabs_to_spaces = self.view.settings().get(
                'translate_tabs_to_spaces'
            )
            indent_string = '\n\n' + (
                ' ' * tab_size if translate_tabs_to_spaces else '\t'
            )
            injection_pt = self.view.find_by_selector('source.cfml meta.class.body')[
                0
            ].begin()

        if is_script:
            injection_pt += 1
        property_string = indent_string + property_string.replace(
            '{name}', property_name
        )
        self.view.insert(edit, injection_pt, property_string)

        if di_property.get('sort_properties', False):
            properties = self.view.find_by_selector('meta.tag.property.cfml')
            property_names = self.view.find_by_selector('meta.tag.property.name.cfml')

            if len(properties) != len(property_names):
                return

            sorted_properties = [
                self.view.substr(r)
                for r, name in sorted(
                    zip(properties, property_names, strict=True),
                    reverse=True,
                    key=lambda x: self.view.substr(x[1]),
                )
            ]

            for i, r in enumerate(reversed(properties)):
                self.view.replace(edit, r, sorted_properties[i])
