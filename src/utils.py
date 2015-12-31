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

def get_last_open_tag(view, pos):
	open_tags = deque()
	tag_starts = [r for r in view.find_by_selector("punctuation.definition.tag.begin") if r.end() <= pos]
	tag_ends = [r for r in view.find_by_selector("punctuation.definition.tag.end") if r.end() <= pos]

	# if lengths don't match don't bother trying to find last open tag
	if len(tag_starts) != len(tag_ends):
		return None

	for tag_start, tag_end in zip(tag_starts, tag_ends):
		tag_name_region = sublime.Region(tag_start.end(), view.find_by_class(tag_start.end(), True, sublime.CLASS_WORD_END, "/>"))
		tag_name = view.substr(tag_name_region)

		# if length is 1 then this is a tag opening punctuation
		if tag_start.size() == 1:

			if tag_end.size() > 1:
				# self closing tag has tag end of size 2 "/>" - skip these
				continue

			# check to exclude cfml tags that should not have a closing tag
			if tag_name in ["cfset","cfelse","cfelseif","cfcontinue","cfbreak","cfthrow","cfrethrow"]:
				continue

			# check to exclude html tags that should not have a closing tag
			if tag_name in ["area","base","br","col","command","embed","hr","img","input","link","meta","param","source"]:
				continue

			open_tags.appendleft(tag_name)

		# if length is 2 then this is a tag closing punctuation
		if tag_start.size() == 2 and tag_name in open_tags:
			open_tags.remove(tag_name)

	return open_tags.popleft() if len(open_tags) > 0 else None

def get_tag_name(view, pos):
	tag_scope = "meta.tag.cfml - punctuation.definition.tag.begin,meta.tag.script.cfml - punctuation.definition.tag.begin"
	tag_name_scope = "entity.name.tag.cfml,entity.name.tag.script.cfml"
	tag_regions = view.find_by_selector(tag_scope)
	tag_name_regions = view.find_by_selector(tag_name_scope)

	for tag_region, tag_name_region in zip(tag_regions, tag_name_regions):
		if tag_region.contains(pos):
			return view.substr(tag_name_region).lower()
	return None

def get_tag_attribute_name(view, pos):
	for scope in ["string.quoted","string.unquoted"]:
		full_scope = "meta.tag.cfml " + scope + ", meta.tag.script.cfml " + scope
		if view.match_selector(pos, full_scope):
			previous_char = get_char_point_before_scope(view, pos, scope)
			break
	else:
		previous_char = get_previous_character(view, pos)

	full_scope = "meta.tag.cfml punctuation.separator.key-value, meta.tag.script.cfml punctuation.separator.key-value"
	if view.match_selector(previous_char, full_scope):
		return get_previous_word(view, previous_char)
	return None

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
