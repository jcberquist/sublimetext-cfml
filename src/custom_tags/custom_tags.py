import sublime, time
from functools import partial
from ..project_index import ProjectIndex
from .. import utils
from . import custom_tag_index

__all__ = ["custom_tags", "get_prefix_completions", "get_tag_completions",
"get_tag_attribute_completions", "get_index_by_tag_name", "get_closing_custom_tags"]


class CustomTags(ProjectIndex):


	def __init__(self):
		super().__init__("custom_tag_folders", {"index": {}, "tags": {}, "completions": {}, "closing_tags": []})


	def new_project(self, project_name, project_data):
		sublime.set_timeout_async(partial(self.index_project, project_name, project_data))


	def index_project(self, project_name, project_data):
		custom_tag_folders = project_data.get("custom_tag_folders", [])
		if len(custom_tag_folders) == 0:
			return

		start_time = time.clock()
		file_count = 0
		index = {}
		tags = {}
		print("CFML: indexing custom tags in project '" + project_name + "'")

		for tag_folder in sorted(custom_tag_folders, key = lambda d: d["path"]):
			root_path = utils.normalize_path(tag_folder["path"])
			index.update(custom_tag_index.index(root_path))

		tags = generate_tag_map(custom_tag_folders, index)
		completions, closing_tags = generate_completions_and_closing_tags(custom_tag_folders, index)

		self.projects[project_name] = {"project_data": project_data, "data": {"index": index, "tags": tags, "completions": completions, "closing_tags": closing_tags}}

		print("CFML: indexing custom tags in project '" + project_name + "' completed - " + str(len(index)) + " files indexed in " + "{0:.2f}".format(time.clock() - start_time) + " seconds")
		self.notify_listeners(project_name)


	def update_project(self, project_name, updated_project_data):
		with self.lock:
			if project_name in self.projects:
				print("CFML: updating project '" + project_name + "'" )
				self.projects[project_name]["project_data"] = updated_project_data

		self.notify_listeners(project_name)


	def update_project_file(self, project_name, file_path):
		file_index = custom_tag_index.index_file(file_path)
		# lock for updating projects
		if project_name in self.projects:
			with self.lock:
				if project_name in self.projects:
					self.projects[project_name]["data"]["index"].update({file_path: file_index})
					custom_tag_folders = self.projects[project_name]["project_data"].get("custom_tag_folders", [])
					index = self.projects[project_name]["data"]["index"]
					tags = generate_tag_map(custom_tag_folders, index)
					completions, closing_tags = generate_completions_and_closing_tags(custom_tag_folders, index)
					self.projects[project_name]["data"]["tags"] = tags
					self.projects[project_name]["data"]["completions"] = completions
					self.projects[project_name]["data"]["closing_tags"] = closing_tags
			self.notify_listeners(project_name)


	def remove_project_file(self, project_name, file_path):
		if project_name in self.projects and file_path in self.projects[project_name]["data"]["index"]:
			with self.lock:
				if project_name in self.projects and file_path in self.projects[project_name]["data"]["index"]:
					del self.projects[project_name]["data"]["index"][file_path]
					custom_tag_folders = self.projects[project_name]["project_data"].get("custom_tag_folders", [])
					index = self.projects[project_name]["data"]["index"]
					tags = generate_tag_map(custom_tag_folders, index)
					completions, closing_tags = generate_completions_and_closing_tags(custom_tag_folders, index)
					self.projects[project_name]["data"]["tags"] = tags
					self.projects[project_name]["data"]["completions"] = completions
					self.projects[project_name]["data"]["closing_tags"] = closing_tags
			self.notify_listeners(project_name)


	def project_deleted(self, project_name):
		self.notify_listeners(project_name)


def generate_tag_map(custom_tag_folders, index):
	tag_map = {}
	for tag_folder in custom_tag_folders:
		root_path = utils.normalize_path(tag_folder["path"])
		for file_path in index:
			if file_path.startswith(root_path):
				tag_map[tag_folder["prefix"] + ":" + index[file_path]["tag_name"]] = file_path
	return tag_map

def generate_completions_and_closing_tags(custom_tag_folders, index):
	prefixes = []
	tags = {}
	attributes = {}
	closing_tags = []

	for tag_folder in custom_tag_folders:
		root_path = utils.normalize_path(tag_folder["path"])
		prefixes.append((tag_folder["prefix"] + '\tcustom tag prefix (cfml)', tag_folder["prefix"] + ":"))
		for file_path in index:
			if file_path.startswith(root_path):
				if tag_folder["prefix"] not in tags:
					tags[tag_folder["prefix"]] = []
				key = tag_folder["prefix"] + ":" + index[file_path]["tag_name"]
				tags[tag_folder["prefix"]].append(make_tag_completion(tag_folder["prefix"], index[file_path]["tag_name"]))
				attributes[key] = [(a + "\t" + index[file_path]["tag_name"], a + "=\"$1\"") for a in index[file_path]["attributes"]]
				if index[file_path]["has_end_tag"]:
					closing_tags.append(key)

	return {"prefixes": prefixes, "tags": tags, "attributes": attributes}, closing_tags

def make_tag_completion(prefix, tag):
	return (tag + "\tcustom tag (" + prefix + ")", tag)

#############

custom_tags = CustomTags()

def get_prefix_completions(project_name):
	if project_name in custom_tags.projects:
		return custom_tags.projects[project_name]["data"]["completions"]["prefixes"]
	return None

def get_tag_completions(project_name, prefix):
	if project_name in custom_tags.projects:
		if prefix in custom_tags.projects[project_name]["data"]["completions"]["tags"]:
			return custom_tags.projects[project_name]["data"]["completions"]["tags"][prefix]
	return None

def get_tag_attribute_completions(project_name, tag_name):
	if project_name in custom_tags.projects:
		if tag_name in custom_tags.projects[project_name]["data"]["completions"]["attributes"]:
			return custom_tags.projects[project_name]["data"]["completions"]["attributes"][tag_name]
	return None

def get_index_by_tag_name(project_name, tag_name):
	if project_name in custom_tags.projects:
		if tag_name in custom_tags.projects[project_name]["data"]["tags"]:
			file_path = custom_tags.projects[project_name]["data"]["tags"][tag_name]
			return file_path, custom_tags.projects[project_name]["data"]["index"][file_path]
	return None, None

def get_closing_custom_tags(project_name):
	if project_name in custom_tags.projects:
		return custom_tags.projects[project_name]["data"]["closing_tags"]
	return []
