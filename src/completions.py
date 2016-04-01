from . import utils
from collections import namedtuple

CompletionList = namedtuple("CompletionList", "completions priority exclude_lower_priority")
completion_sources = {"tag": [], "tag_attributes": [], "script": [], "dot": []}

def add_completion_source(source_type, callback):
	completion_sources[source_type].append(callback)

def get_completions(source_type, *args):
	completion_lists = []
	minimum_priority = 0

	for callback in completion_sources[source_type]:
		completionlist = callback(*args)
		if completionlist:
			completion_lists.append(completionlist)
			if completionlist.exclude_lower_priority:
				minimum_priority = completionlist.priority

	full_completion_list = []
	for completionlist in sorted(completion_lists, key=lambda comp_list: comp_list.priority, reverse=True):
		if completionlist.priority >= minimum_priority:
			full_completion_list.extend(completionlist.completions)

	return full_completion_list

def get_base_info(view, prefix, position):
	file_path = view.file_name().replace("\\", "/") if view.file_name() else None
	file_name = file_path.split("/").pop().lower() if file_path else None
	project_name = utils.get_project_name(view)
	prefix_start = position - len(prefix)
	previous_char = view.substr(prefix_start - 1)
	return {"file_path": file_path, "file_name": file_name, "project_name": project_name, "prefix_start": prefix_start, "previous_char": previous_char}

def get_tag_completions(view, prefix, position):
	info = get_base_info(view, prefix, position)
	is_inside_tag = view.match_selector(info["prefix_start"], "meta.tag - punctuation.definition.tag.begin")
	is_tag_name = view.match_selector(info["prefix_start"] - 1, "punctuation.definition.tag.begin, entity.name.tag")

	if is_inside_tag and not is_tag_name:
		info.update({"tag_in_script": False, "tag_name": utils.get_tag_name(view, info["prefix_start"]), "tag_attribute_name": utils.get_tag_attribute_name(view, info["prefix_start"]) })
		return get_completions('tag_attributes', view, prefix, position, info)

	completions = get_completions('tag', view, prefix, position, info)

	# if the opening < is not here insert that
	# note that a custom tag prefix will be split at `:`
	# so that has to be checked too
	if info["previous_char"] not in ["<", ":"]:
		completions = [(pair[0], "<" + pair[1]) for pair in completions]

	return completions

def get_script_completions(view, prefix, position):
	info = get_base_info(view, prefix, position)
	return get_completions('script', view, prefix, position, info)

def get_script_tag_attributes(view, prefix, position):
	info = get_base_info(view, prefix, position)
	info["tag_in_script"] = True
	info["tag_name"] = "component" if view.match_selector(info["prefix_start"], "meta.class.declaration") else utils.get_tag_name(view, info["prefix_start"])
	info["tag_attribute_name"] = utils.get_tag_attribute_name(view, info["prefix_start"])
	return get_completions('tag_attributes', view, prefix, position, info)

def get_dot_completions(view, prefix, position):
	info = get_base_info(view, prefix, position)
	info["dot_context"] = utils.get_dot_context(view, info["prefix_start"] - 1)
	return get_completions('dot', view, prefix, position, info)
