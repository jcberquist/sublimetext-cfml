import sublime, sublime_plugin
from . import cfcs, documentation
from .. import utils

class CfmlDiPropertyCommand(sublime_plugin.TextCommand):

	def run(self, edit, property_name=None):

		pt = self.view.sel()[0].begin()

		if not self.view.match_selector(pt, "source.cfml meta.class"):
			return

		if property_name:
			self.insert_property(edit, property_name)
			return

		project_name = utils.get_project_name(self.view)
		if not project_name:
			return

		# cfc_info, metadata, function_name = find_cfc(view, position, project_name)
		cfc_info, metadata, function_name = documentation.find_cfc(self.view, pt, project_name)

		if cfc_info:
			self.insert_property(edit, cfc_info["name"])
		else:
			cfc_list = cfcs.get_cfc_list(project_name)
			def callback(i):
				if i > -1:
					self.view.run_command("cfml_di_property", {"property_name": cfc_list[i]})

			self.view.window().show_quick_panel(cfc_list, callback, flags=sublime.MONOSPACE_FONT)

	def insert_property(self, edit, property_name):
		di_property = utils.get_setting("di_property")
		is_script = len(self.view.find_by_selector("source.cfml.script meta.class.body.cfml")) > 0
		property_string = di_property.get("script_template", "") if is_script else di_property.get("tag_template", "")

		if "{name}" not in property_string:
			return

		properties = self.view.find_by_selector("meta.tag.property.cfml")
		property_names = [self.view.substr(r).lower() for r in self.view.find_by_selector("meta.tag.property.name.cfml")]

		if property_name.lower() in property_names:
			return

		if len(properties) > 0:
			indent_region = sublime.Region(self.view.line(properties[-1]).begin(), properties[-1].begin())
			indent_string = "\n" + self.view.substr(indent_region)
			injection_pt = properties[-1].end()
		else:
			tab_size = self.view.settings().get("tab_size")
			translate_tabs_to_spaces = self.view.settings().get("translate_tabs_to_spaces")
			indent_string = "\n\n" + (" " * tab_size if translate_tabs_to_spaces else "\t")
			injection_pt = self.view.find_by_selector("source.cfml meta.class.body")[0].begin()

		if is_script:
			injection_pt += 1
		property_string = indent_string + property_string.replace("{name}", property_name)
		self.view.insert(edit, injection_pt, property_string)

		if di_property.get("sort_properties", False):
			properties = self.view.find_by_selector("meta.tag.property.cfml")
			property_names = self.view.find_by_selector("meta.tag.property.name.cfml")

			if len(properties) != len(property_names):
				return

			sorted_properties = [self.view.substr(r) for r, name in sorted(zip(properties, property_names), reverse=True, key=lambda x: self.view.substr(x[1]))]

			for i, r in enumerate(reversed(properties)):
				self.view.replace(edit, r, sorted_properties[i])

