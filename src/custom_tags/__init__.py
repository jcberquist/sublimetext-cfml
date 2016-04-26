from .. import completions, inline_documentation, goto_cfml_file, utils
from .custom_tags import *
from .documentation import get_inline_documentation, get_goto_cfml_file


def plugin_loaded():
	custom_tags.sync_projects()
	completions.add_completion_source('tag', get_tags)
	completions.add_completion_source('tag_attributes', get_tag_attributes)
	inline_documentation.add_documentation_source(get_inline_documentation)
	goto_cfml_file.add_goto_source(get_goto_cfml_file)
	utils.get_closing_custom_tags = get_closing_custom_tags

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
	if not info["tag_name"]:
		return None

	if ":" in info["tag_name"] and info["project_name"] in custom_tags.projects:
		completion_list = get_tag_attribute_completions(info["project_name"], info["tag_name"])
		if completion_list:
			return completions.CompletionList(completion_list, 0, False)
	return None
