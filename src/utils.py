import sublime
from collections import deque, namedtuple
from os.path import dirname, realpath

path_parts = dirname(realpath(__file__)).replace("\\", "/").split("/")
CFML_PLUGIN_NAME = path_parts[-1].split(".")[0] if "Installed Packages" in path_parts else path_parts[-2]

Symbol = namedtuple('Symbol', 'name is_function function_region args_region')

def get_plugin_name():
	return CFML_PLUGIN_NAME

def get_previous_character(view, position):
	if view.substr(position - 1) in [" ", "\t", "\n"]:
		position = view.find_by_class(position, False, sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END)
	return position - 1

def get_next_character(view, position):
	if view.substr(position) in [" ", "\t", "\n"]:
		position = view.find_by_class(position, True, sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START)
	return position

def get_previous_word(view, position):
	previous_character = get_previous_character(view, position)
	return view.substr(view.word(previous_character)).lower()

def get_scope_region_containing_point(view, pt, scope):
	scope_count = view.scope_name(pt).count(scope)
	if scope_count == 0:
		return None
	scope_to_find = " ".join([scope] * scope_count)
	for r in view.find_by_selector(scope_to_find):
		if r.contains(pt):
			return r
	return None

def get_char_point_before_scope(view, pt, scope):
	scope_region = get_scope_region_containing_point(view, pt, scope)
	if scope_region:
		scope_start = scope_region.begin()
		return get_previous_character(view, scope_start)
	return None

def get_dot_context(view, dot_position):
	context = []

	if view.substr(dot_position) != ".":
		return context

	if view.substr(dot_position - 1) in [" ", "\t", "\n"]:
		dot_position = view.find_by_class(dot_position, False, sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END)

	for scope_name in ["meta.support.function-call", "meta.function-call"]:
		base_scope_count = view.scope_name(dot_position).count(scope_name)
		scope_to_find = " ".join([scope_name] * (base_scope_count + 1))
		if view.match_selector(dot_position - 1, scope_to_find):
			function_name, name_region, function_args_region = get_function_call(view, dot_position - 1, scope_name == "meta.support.function-call")
			context.append(Symbol(function_name, True, name_region, function_args_region))
			break
	else:
		if view.match_selector(dot_position - 1, "variable, meta.property.object"):
			name_region = view.word(dot_position)
			context.append(Symbol(view.substr(name_region).lower(), False, None, None))

	if len(context) > 0:
		context.extend(get_dot_context(view, name_region.begin() - 1))

	return context

def get_struct_context(view, position):
	context = []

	if not view.match_selector(position, "meta.group.braces.curly"):
		return context

	previous_char_point = get_char_point_before_scope(view, position, "meta.group.braces.curly")
	if not view.match_selector(previous_char_point, "keyword.operator.assignment.cfml,punctuation.separator.key-value.cfml"):
		return context

	previous_char_point = get_previous_character(view, previous_char_point)

	if not view.match_selector(previous_char_point, "meta.property.object.cfml,variable,string.unquoted.label.cfml"):
		return context

	name_region = view.word(previous_char_point)
	context.append(Symbol(view.substr(name_region).lower(), False, None, None))

	if view.match_selector(previous_char_point, "meta.property.object.cfml"):
		context.extend(get_dot_context(view, name_region.begin() - 1))
	else:
		context.extend(get_struct_context(view, name_region.begin()))

	return context

def get_setting(setting_key):
	cfml_settings = sublime.load_settings("cfml_package.sublime-settings")
	return cfml_settings.get(setting_key)

def get_tag_end(view, pos, is_cfml):
	tag_end = view.find("/?>", pos)
	if tag_end:
		if view.match_selector(tag_end.begin(), "punctuation.definition.tag"):
			tag_end_is_cfml = view.match_selector(tag_end.begin(), "punctuation.definition.tag.end.cfml")
			if is_cfml == tag_end_is_cfml:
				return tag_end
		return get_tag_end(view, tag_end.end(), is_cfml)
	return None

def get_last_open_tag(view, pos, cfml_only):
	tag_selector = "entity.name.tag.cfml" if cfml_only else "entity.name.tag"
	closed_tags = []
	cfml_non_closing_tags = get_setting("cfml_non_closing_tags")
	html_non_closing_tags = get_setting("html_non_closing_tags")

	tag_name_regions = reversed([r for r in view.find_by_selector(tag_selector) if r.end() <= pos])

	for tag_name_region in tag_name_regions:
		# check for closing tag
		if view.substr(tag_name_region.begin() - 1) == "/":
			closed_tags.append(view.substr(tag_name_region))
			continue

		# this is an opening tag
		is_cfml = view.match_selector(tag_name_region.begin(), "entity.name.tag.cfml")
		tag_end = get_tag_end(view, tag_name_region.end(), is_cfml)

		# if no tag end then give up
		if not tag_end:
			return None

		# if tag_end is after cursor position, then ignore it
		if tag_end.begin() > pos:
			continue

		# if tag_end length is 2 then this is a self closing tag so ignore it
		if tag_end.size() == 2:
			continue

		tag_name = view.substr(tag_name_region)

		if tag_name in closed_tags:
			closed_tags.remove(tag_name)
			continue

		# check to exclude cfml tags that should not have a closing tag
		if tag_name in cfml_non_closing_tags:
			continue
		# check to exclude html tags that should not have a closing tag
		if tag_name in html_non_closing_tags:
			continue

		return tag_name

	return None

def get_tag_name(view, pos):
	tag_scope = "meta.tag.cfml - punctuation.definition.tag.begin, meta.tag.script.cfml, meta.tag.script.cf.cfml"
	tag_name_scope = "entity.name.tag.cfml, entity.name.tag.script.cfml"
	tag_regions = view.find_by_selector(tag_scope)
	tag_name_regions = view.find_by_selector(tag_name_scope)

	for tag_region, tag_name_region in zip(tag_regions, tag_name_regions):
		if tag_region.contains(pos):
			return view.substr(tag_name_region).lower()
	return None

def get_tag_attribute_name(view, pos):
	for scope in ["string.quoted","string.unquoted"]:
		full_scope = "meta.tag.cfml " + scope + ", meta.tag.script.cfml " + scope + ", meta.tag.script.cf.cfml " + scope
		if view.match_selector(pos, full_scope):
			previous_char = get_char_point_before_scope(view, pos, scope)
			break
	else:
		previous_char = get_previous_character(view, pos)

	full_scope = "meta.tag.cfml punctuation.separator.key-value, meta.tag.script.cfml punctuation.separator.key-value, meta.tag.script.cf.cfml punctuation.separator.key-value"
	if view.match_selector(previous_char, full_scope):
		return get_previous_word(view, previous_char)
	return None

def between_cfml_tag_pair(view, pos):
	if not view.substr(pos - 1) == ">" or not view.substr(sublime.Region(pos, pos + 2)) == "</":
		return False
	if not view.match_selector(pos - 1, "meta.tag.cfml") or not view.match_selector(pos + 2, "meta.tag.cfml"):
		return False
	if get_tag_name(view, pos - 1) != get_tag_name(view, pos + 2):
		return False
	return True

def get_function(view, pt):
	function_scope = "meta.function.cfml"
	function_name_scope = "entity.name.function.cfml,entity.name.function.constructor.cfml"
	function_region = get_scope_region_containing_point(view, pt, function_scope)
	if function_region:
		function_name_regions = view.find_by_selector(function_name_scope)
		for function_name_region in function_name_regions:
			if function_region.contains(function_name_region):
				return view.substr(function_name_region).lower(), function_name_region, function_region
	return None

def get_function_call(view, pt, support_function = False):
	function_call_scope = "meta.support.function-call" if support_function else "meta.function-call"
	function_region = get_scope_region_containing_point(view, pt, function_call_scope)
	if function_region:
		function_name_region = view.word(function_region.begin())
		function_args_region = sublime.Region(function_name_region.end(), function_region.end())
		return view.substr(function_name_region).lower(), function_name_region, function_args_region
	return None
