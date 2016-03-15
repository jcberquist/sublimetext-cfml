import sublime, sublime_plugin, webbrowser
from .src.bootstrap import *
from .src import completions, events, utils

class CfmlEventListener(sublime_plugin.EventListener):

	def on_load_async(self, view):
		events.trigger('on_load_async', view)

	def on_close(self, view):
		events.trigger('on_close', view)

	def on_post_save_async(self, view):
		events.trigger('on_post_save_async', view)

	def on_post_text_command(self, view, command_name, args):
		if command_name == "commit_completion":
			pos = view.sel()[0].begin()

			if view.match_selector(pos, "meta.tag.cfml -source.cfml.script, meta.tag.script.cfml, meta.tag.script.cf.cfml, meta.class.declaration.cfml -meta.class.inheritance.cfml"):
				if view.substr(pos - 1) in [" ", "\"", "'", "="]:
					view.run_command("auto_complete", {"api_completions_only": True})
				elif view.substr(pos) == "\"":
					# an attribute completion was most likely just inserted
					# advance cursor past double quote character
					view.run_command("move", {"by": "characters", "forward": True})

			if view.substr(pos - 1) == ":" and view.match_selector(pos - 1, "meta.tag.custom.cfml -source.cfml.script"):
				view.run_command("auto_complete", {"api_completions_only": True})

			if view.substr(pos - 1) == "." and view.match_selector(pos - 1, "meta.support.function-call.createcomponent.cfml string.quoted, entity.other.inherited-class.cfml, meta.instance.constructor.cfml"):
				view.run_command("auto_complete", {"api_completions_only": True})

	def on_post_window_command(self, window, command_name, args):
		events.trigger('on_post_window_command', window, command_name, args)

	def on_query_completions(self, view, prefix, locations):
		if not view.match_selector(locations[0], "embedding.cfml"):
			return None

		prefix_start = locations[0] - len(prefix)
		base_script_scope = "embedding.cfml source.cfml.script"

		# tag completions
		if view.match_selector(prefix_start, "embedding.cfml - source.cfml.script"):
			tag_completions = completions.get_tag_completions(view, prefix, locations[0])
			return tag_completions

		# dot completions (member and model function completions)
		if view.match_selector(prefix_start - 1, base_script_scope + " punctuation.accessor.cfml"):
			completion_list = completions.get_dot_completions(view, prefix, locations[0])
			return completion_list

		# tag in script attribute completions
		if view.match_selector(prefix_start, base_script_scope + " meta.tag, " + base_script_scope + " meta.class.declaration"):
			attribute_completions = completions.get_script_tag_attributes(view, prefix, locations[0])
			return attribute_completions

		# script completions
		if view.match_selector(prefix_start, "embedding.cfml source.cfml.script"):
			completion_list = completions.get_script_completions(view, prefix, locations[0])
			return completion_list

		# default
		return None

class CloseCfmlTagCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		for sel in self.view.sel():
			pt = sel.begin()
			cfml_only = self.view.match_selector(pt, "string")
			last_open_tag = utils.get_last_open_tag(self.view,pt - 1, cfml_only)
			if last_open_tag:
				self.view.insert(edit,pt,"/" + last_open_tag + ">")
			else:
				# if there is no open tag print "/"
				self.view.insert(edit,pt,"/")

class CfmlAutoInsertClosingTagCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		pt = self.view.sel()[0].begin()
		if utils.get_setting("cfml_auto_insert_closing_tag"):
			tag_name = utils.get_tag_name(self.view, pt)
			if tag_name:
				is_custom_tag = self.view.match_selector(pt, "meta.tag.custom.cfml")
				if is_custom_tag:
					closing_custom_tags = utils.get_closing_custom_tags_by_project(self.view)
					has_closing_tag = tag_name in closing_custom_tags
				else:
					cfml_non_closing_tags = utils.get_setting("cfml_non_closing_tags")
					has_closing_tag = tag_name not in cfml_non_closing_tags
				if has_closing_tag:
					next_char = utils.get_next_character(self.view, pt)
					tag_close_search_region = self.view.find("</" + tag_name + ">", pt)
					if next_char != tag_close_search_region.begin():
						self.view.run_command("insert_snippet", {"contents": ">$0</" + tag_name + ">"})
						return
		self.view.run_command("insert_snippet", {"contents": ">"})

class CfmlBetweenTagPairCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		pt = self.view.sel()[0].begin()
		cfml_between_tag_pair = utils.get_setting("cfml_between_tag_pair")
		if cfml_between_tag_pair in ["newline","indent"] and utils.between_cfml_tag_pair(self.view, pt):
			self.view.run_command("insert_snippet", {"contents": "\n" + ("\t" if cfml_between_tag_pair == "indent" else "") + "$0\n"})
			return
		self.view.run_command("insert_snippet", {"contents": "\n"})

class CfmlOpenPackageFileCommand(sublime_plugin.WindowCommand):

	def run(self, file):
		package_file = file.replace("{cfml_package_name}", utils.get_plugin_name())
		self.window.run_command("open_file", {"file": package_file})
