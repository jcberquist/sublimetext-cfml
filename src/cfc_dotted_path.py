import sublime, sublime_plugin

class CfmlCfcDottedPathCommand(sublime_plugin.WindowCommand):
	def run(self, files):
		file_paths = [self.dotted_path(file_path) for file_path in self.cfc_files(files)]
		sublime.set_clipboard("\n".join(file_paths))
		sublime.status_message("CFML: copied cfc dotted path")

	def is_visible(self, files):
		return len(self.cfc_files(files)) > 0

	def is_enabled(self, files):
		if self.window.project_data() and "folders" in self.window.project_data() and len(self.window.project_data()["folders"]) > 0:
			return True
		return False

	def cfc_files(self, files):
		return [file_path for file_path in files if file_path.split(".")[-1] == "cfc"]

	def dotted_path(self, file_path):
		normalized_path = file_path.replace("\\", "/")
		for folder in self.window.project_data()["folders"]:
			relative_path = normalized_path.replace(folder["path"].replace("\\", "/"), "")
			if relative_path != normalized_path:
				if relative_path.startswith("/"):
					relative_path = relative_path[1:]
				return relative_path.split(".")[0].replace("/", ".")
		return ""
