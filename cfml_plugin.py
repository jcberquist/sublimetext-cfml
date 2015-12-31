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
			if view.match_selector(pos, "embedding.cfml meta.tag.cfml - source.cfml.script, embedding.cfml meta.tag.script.cfml"):
				view.run_command("auto_complete", {"api_completions_only": True})

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
		if view.match_selector(prefix_start - 1, base_script_scope + " keyword.operator.accessor.cfml"):
			completion_list = completions.get_dot_completions(view, prefix, locations[0])
			return completion_list

		#tag in script attribute completions
		if view.match_selector(prefix_start, base_script_scope + " meta.tag, " + base_script_scope + " meta.class"):
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
		pt = self.view.sel()[0].begin()
		last_open_tag = utils.get_last_open_tag(self.view,pt - 1)
		if last_open_tag:
			self.view.insert(edit,pt,"/" + last_open_tag + ">")
		else:
			# if there is no open tag print "/"
			self.view.insert(edit,pt,"/")

class CfmlDefaultPackageSettingsCommand(sublime_plugin.WindowCommand):

	def run(self):
		self.window.run_command("open_file", {"file": "${packages}/" + utils.get_plugin_name() + "/settings/cfml_package.sublime-settings"})
