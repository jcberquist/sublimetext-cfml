import sublime
from .. import completions, inline_documentation
from .custom_tags import *
from .documentation import get_inline_documentation


def plugin_loaded():
	custom_tags.sync_projects()
	completions.add_completion_source('tag', get_tags)
	completions.add_completion_source('tag_attributes', get_tag_attributes)
	inline_documentation.add_documentation_source(get_inline_documentation)

def get_tags(view, prefix, position, info):
	if (info["previous_char"] == "<"):
		completion_list = get_prefix_completions(info["project_name"])
		if completion_list:
			return completions.CompletionList(completion_list, 0, False)
	elif (info["previous_char"] == ":"):
		prefix = view.substr(view.word(info["prefix_start"] - 1))
		completion_list = get_tag_completions(info["project_name"], prefix)
		if completion_list:
			return completions.CompletionList(completion_list, 0, False)
	return None

def get_tag_attributes(view, prefix, position, info):
	if ":" in info["tag_name"] and info["project_name"] in custom_tags.projects:
		completion_list = get_tag_attribute_completions(info["project_name"], info["tag_name"])
		if completion_list:
			return completions.CompletionList(completion_list, 0, False)
	return None
