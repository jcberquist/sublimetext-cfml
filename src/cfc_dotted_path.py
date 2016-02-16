import sublime, sublime_plugin
from . import utils

class CfmlCfcDottedPathCommand(sublime_plugin.WindowCommand):
	def run(self, files):

		def on_done(i):
			if i != -1:
				sublime.set_clipboard(dotted_paths[i])
				sublime.status_message("CFML: copied cfc dotted path")

		dotted_paths = self.dotted_paths(self.cfc_files(files)[0])

		if len(dotted_paths) > 1:
			self.window.show_quick_panel(dotted_paths, on_done)
		else:
			on_done(0)

	def is_visible(self, files):
		return len(self.cfc_files(files)) == 1

	def is_enabled(self, files):
		if self.window.project_data() and "folders" in self.window.project_data() and len(self.window.project_data()["folders"]) > 0:
			return True
		return False

	def cfc_files(self, files):
		return [file_path for file_path in files if file_path.split(".")[-1] == "cfc"]

	def dotted_paths(self, file_path):
		dotted_paths = []
		normalized_path = utils.normalize_path(file_path)
		project_data = self.window.project_data()
		if "mappings" in project_data:
			for mapping in project_data["mappings"]:
				normalized_mapping = utils.normalize_mapping(mapping)
				if normalized_path.startswith(normalized_mapping["path"]):
					mapped_path = normalized_mapping["mapping"] + normalized_path.replace(normalized_mapping["path"], "")
					path_parts = mapped_path.split("/")[1:]
					dotted_paths.append(".".join(path_parts)[:-4])

		# fall back to folders if no mappings matched
		if len(dotted_paths) == 0:
			for folder in self.window.project_data()["folders"]:
				relative_path = normalized_path.replace(utils.normalize_path(folder["path"]), "")
				if relative_path != normalized_path:
					path_parts = relative_path.split("/")[1:]
					dotted_paths.append(".".join(path_parts)[:-4])

		return dotted_paths
