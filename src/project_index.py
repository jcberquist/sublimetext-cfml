import sublime, threading
from . import events, utils

class ProjectIndex():

	def __init__(self, folder_key, default_data_dict):
		self.lock = threading.Lock()
		self.projects = {}
		self.listeners = []
		self.folder_key = folder_key
		self.default_data_dict = default_data_dict

		events.subscribe('on_load_async', lambda view: self.sync_projects())
		events.subscribe('on_close', lambda view: self.sync_projects())
		events.subscribe('on_post_save_async', self.on_post_save_async)
		events.subscribe('on_post_window_command', self.on_post_window_command)

	def subscribe(self, listener):
		self.listeners.append(listener)

	def notify_listeners(self, project_name):
		for listener in self.listeners:
			listener(project_name)

	def sync_projects(self):
		project_list = utils.get_project_list()

		with self.lock:
			current_project_names = set(self.projects.keys())
			updated_project_names = {project_name for project_name, project_data in project_list}
			#print(current_project_names,updated_project_names)
			new_project_names = list(updated_project_names.difference(current_project_names))
			stale_project_names = list(current_project_names.difference(updated_project_names))
			#print(new_project_names,stale_project_names)
			# remove stale projects
			for project_name in stale_project_names:
				del self.projects[project_name]
			# add new projects
			for project_name, project_data in project_list:
				if project_name in new_project_names:
					self.projects[project_name] = {"project_data": project_data, "data": dict(self.default_data_dict)}
		# now that projects dict is up to date release lock before initing directory load
		for project_name, project_data in project_list:
			if project_name in new_project_names:
				self.new_project(project_name, project_data)


	def on_post_save_async(self, view):
		file_name = view.file_name().replace("\\","/")
		# check to see if the updated file was a .sublime-project
		if file_name.lower().endswith(".sublime-project"):
			# trying this without try/catch so that errors show in the console
			project_name = utils.extract_project_name(file_name)
			project_data = sublime.decode_value(view.substr(sublime.Region(0, view.size())))
			self.project_updated(project_name, project_data)
		else:
			project_name = utils.get_project_name(view)
			if project_name:
				self.project_file_updated(project_name, file_name)


	def on_post_window_command(self, window, command, args):
		if command == "delete_file":
			window_project_name = utils.get_project_name_from_window(window)
			if window_project_name:
				for file_name in args["files"]:
					if not file_name.lower().endswith(".sublime-project"):
						self.remove_project_file(window_project_name, file_name.replace("\\","/"))

			for file_name in args["files"]:
				if file_name.lower().endswith(".sublime-project"):
					project_name = utils.extract_project_name(file_name)
					if project_name in self.projects:
						with self.lock:
							if project_name in self.projects:
								del self.projects[project_name]
						self.project_deleted(project_name)


	def project_updated(self, project_name, updated_project_data):
		if project_name not in self.projects:
			self.sync_projects()
			return

		# if this project has already been indexed, reindexing should only be
		# necessary if the model folder paths have changed
		new_paths = [utils.normalize_path(folder["path"]) for folder in updated_project_data.get(self.folder_key, [])]
		current_paths = [utils.normalize_path(folder["path"]) for folder in self.projects[project_name]["project_data"].get(self.folder_key, [])]
		if set(new_paths) != set(current_paths):
			with self.lock:
				if project_name in self.projects:
					del self.projects[project_name]
			self.sync_projects()
		else:
			# project file has been updated (saved), but no folder paths were changed
			# so update project_data
			self.update_project(project_name, updated_project_data)

	def project_file_updated(self, project_name, file_path):
		if project_name not in self.projects:
			return
		project_data = self.projects[project_name]["project_data"]
		# check for tracked file path
		tracked_folders = project_data.get(self.folder_key, [])
		for tracked_folder in tracked_folders:
			root_path = utils.normalize_path(tracked_folder["path"])
			if file_path.startswith(root_path):
				break
		else:
			return

		# if we got here this is a tracked project file
		self.update_project_file(project_name, file_path)


	## methods for child classes to implement


	def new_project(self, project_name, project_data):
		pass


	def update_project(self, project_name, updated_project_data):
		pass


	def update_project_file(self, project_name, file_path):
		pass


	def remove_project_file(self, project_name, file_path):
		pass


	def project_deleted(self, project_name):
		pass
