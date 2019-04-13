import sublime
import os
from collections import namedtuple

Symbol = namedtuple(
    "Symbol", "name is_function function_region args_region name_region"
)


def get_plugin_name():
    return __package__.split(".")[0]


def get_project_list():
    project_list = []
    for window in sublime.windows():
        if window.project_file_name():
            project_tuple = (
                normalize_path(window.project_file_name()),
                window.project_data(),
            )
            project_list.append(project_tuple)
    return project_list


def get_project_name(view):
    project_file_name = view.window().project_file_name()
    if project_file_name:
        return normalize_path(project_file_name)
    return None


def get_project_name_from_window(window):
    project_file_name = window.project_file_name()
    if project_file_name:
        return normalize_path(project_file_name)
    return None


def normalize_path(path, root_path=None):
    if path is None:
        return None
    if not os.path.isabs(path) and root_path is not None:
        path = os.path.normpath(os.path.join(root_path, path))
    normalized_path = path.replace("\\", "/")
    if len(normalized_path) > 0 and normalized_path[-1] == "/":
        normalized_path = normalized_path[:-1]
    return normalized_path


def normalize_mapping(mapping, root_path=None):
    normalized_mapping = {}
    # convenience check for project file path
    if root_path.endswith("sublime-project"):
        root_path = os.path.dirname(root_path)
    normalized_mapping["path"] = normalize_path(mapping["path"], root_path)
    normalized_mapping_path = mapping["mapping"].replace("\\", "/")
    if normalized_mapping_path[0] != "/":
        normalized_mapping_path = "/" + normalized_mapping_path
    if normalized_mapping_path[-1] == "/":
        normalized_mapping_path = normalized_mapping_path[:-1]
    normalized_mapping["mapping"] = normalized_mapping_path
    return normalized_mapping


def format_lookup_file_path(file_path):
    file_path = normalize_path(file_path)
    if file_path[1] == ":":
        file_path = "/" + file_path[0] + file_path[2:]
    return file_path


def get_previous_character(view, position):
    if view.substr(position - 1) in [" ", "\t", "\n"]:
        position = view.find_by_class(
            position, False, sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END
        )
    return position - 1


def get_next_character(view, position):
    if view.substr(position) in [" ", "\t", "\n"]:
        position = view.find_by_class(
            position, True, sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START
        )
    return position


def get_previous_word(view, position):
    previous_character = get_previous_character(view, position)
    return view.substr(view.word(previous_character)).lower()


def get_scope_region_containing_point(view, pt, scope):
    scope_count = view.scope_name(pt).count(scope) - view.scope_name(pt).count(
        "." + scope
    )
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
        dot_position = view.find_by_class(
            dot_position, False, sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END
        )

    base_scope_count = view.scope_name(dot_position).count("meta.function-call")
    scope_to_find = " ".join(["meta.function-call"] * (base_scope_count + 1))
    if view.match_selector(dot_position - 1, scope_to_find):
        function_name, name_region, function_args_region = get_function_call(
            view, dot_position - 1
        )
        context.append(
            Symbol(function_name, True, name_region, function_args_region, name_region)
        )
    elif view.match_selector(
        dot_position - 1, "variable, meta.property, meta.instance.constructor"
    ):
        name_region = view.word(dot_position)
        context.append(
            Symbol(view.substr(name_region).lower(), False, None, None, name_region)
        )

    if len(context) > 0:
        context.extend(get_dot_context(view, name_region.begin() - 1))

    return context


def get_struct_context(view, position):
    context = []

    if not view.match_selector(position, "meta.struct-literal.cfml"):
        return context

    previous_char_point = get_char_point_before_scope(
        view, position, "meta.struct-literal.cfml"
    )
    if not view.match_selector(
        previous_char_point,
        "keyword.operator.assignment.binary.cfml,punctuation.separator.key-value.cfml",
    ):
        return context

    previous_char_point = get_previous_character(view, previous_char_point)

    if not view.match_selector(
        previous_char_point, "meta.property,variable,meta.struct-literal.key.cfml"
    ):
        return context

    name_region = view.word(previous_char_point)
    context.append(
        Symbol(view.substr(name_region).lower(), False, None, None, name_region)
    )

    if view.match_selector(previous_char_point, "meta.property"):
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
            tag_end_is_cfml = view.match_selector(
                tag_end.begin(), "punctuation.definition.tag.end.cfml"
            )
            if is_cfml == tag_end_is_cfml:
                return tag_end
        return get_tag_end(view, tag_end.end(), is_cfml)
    return None


def get_last_open_tag(view, pos, cfml_only, custom_tag_index):
    tag_selector = (
        "entity.name.tag.cfml, entity.name.tag.custom.cfml"
        if cfml_only
        else "entity.name.tag"
    )
    closed_tags = []
    cfml_non_closing_tags = get_setting("cfml_non_closing_tags")
    html_non_closing_tags = get_setting("html_non_closing_tags")

    tag_name_regions = reversed(
        [r for r in view.find_by_selector(tag_selector) if r.end() <= pos]
    )

    for tag_name_region in tag_name_regions:
        # check for closing tag
        if view.substr(tag_name_region.begin() - 1) == "/":
            closed_tags.append(view.substr(tag_name_region))
            continue

        # this is an opening tag
        is_cfml = view.match_selector(
            tag_name_region.begin(), "entity.name.tag.cfml, entity.name.tag.custom.cfml"
        )
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
        # check for custom tags that should not be closed
        if view.match_selector(
            tag_name_region.begin(), "meta.tag.custom.cfml"
        ) and tag_name not in custom_tag_index.get_closing_custom_tags(
            get_project_name(view)
        ):
            continue

        return tag_name

    return None


def get_tag_name(view, pos):
    tag_scope = "meta.tag.cfml - punctuation.definition.tag.begin, meta.tag.custom.cfml - punctuation.definition.tag.begin, meta.tag.script.cfml, meta.tag.script.cf.cfml"
    tag_name_scope = (
        "entity.name.tag.cfml, entity.name.tag.custom.cfml, entity.name.tag.script.cfml"
    )
    tag_regions = view.find_by_selector(tag_scope)
    tag_name_regions = view.find_by_selector(tag_name_scope)

    for tag_region, tag_name_region in zip(tag_regions, tag_name_regions):
        if tag_region.contains(pos):
            return view.substr(tag_name_region).lower()
    return None


def get_tag_attribute_name(view, pos):
    if view.match_selector(
        pos,
        "meta.tag entity.other.attribute-name.cfml, meta.class.declaration.cfml entity.other.attribute-name.cfml",
    ):
        return view.substr(view.word(pos)).lower()

    for scope in ["string.quoted", "string.unquoted"]:
        full_scope = (
            "meta.tag.cfml "
            + scope
            + ", meta.tag.custom.cfml "
            + scope
            + ", meta.tag.script.cfml "
            + scope
            + ", meta.tag.script.cf.cfml "
            + scope
            + ", meta.class.declaration.cfml "
            + scope
        )
        if view.match_selector(pos, full_scope):
            pos = get_char_point_before_scope(view, pos, scope)
            break

    full_scope = [
        "meta.tag.cfml punctuation.separator.key-value",
        "meta.tag.custom.cfml punctuation.separator.key-value",
        "meta.tag.script.cfml punctuation.separator.key-value",
        "meta.tag.script.cf.cfml punctuation.separator.key-value",
        "meta.class.declaration.cfml punctuation.separator.key-value",
    ]
    if view.match_selector(pos, ",".join(full_scope)):
        return get_previous_word(view, pos)

    return None


def between_cfml_tag_pair(view, pos):
    if (
        not view.substr(pos - 1) == ">"
        or not view.substr(sublime.Region(pos, pos + 2)) == "</"
    ):
        return False
    if not view.match_selector(
        pos - 1, "meta.tag.cfml, meta.tag.custom.cfml"
    ) or not view.match_selector(pos + 2, "meta.tag.cfml, meta.tag.custom.cfml"):
        return False
    if get_tag_name(view, pos - 1) != get_tag_name(view, pos + 2):
        return False
    return True


def get_function(view, pt):
    if view.match_selector(pt, "meta.function.cfml"):
        function_scope = "meta.function.cfml"
    else:
        function_scope = "meta.function.declaration.cfml"

    function_name_scope = (
        "entity.name.function.cfml,entity.name.function.constructor.cfml"
    )
    function_region = get_scope_region_containing_point(view, pt, function_scope)
    if function_region:
        function_name_regions = view.find_by_selector(function_name_scope)
        for function_name_region in function_name_regions:
            if function_region.contains(function_name_region):
                return (
                    view.substr(function_name_region).lower(),
                    function_name_region,
                    function_region,
                )
    return None


def get_function_call(view, pt, support=False):
    function_call_scope = "meta.function-call"
    if support:
        function_call_scope += ".support"
    function_region = get_scope_region_containing_point(view, pt, function_call_scope)
    if function_region:
        function_name_region = view.word(function_region.begin())
        function_args_region = sublime.Region(
            function_name_region.end(), function_region.end()
        )
        return (
            view.substr(function_name_region).lower(),
            function_name_region,
            function_args_region,
        )
    return None


def get_current_function_body(view, pt, component_method=True):
    selector = "meta.function.body"
    if component_method:
        selector = "meta.class.body " + selector
    return get_scope_region_containing_point(view, pt, selector)


def find_variable_assignment(view, position, variable_name):
    regex_prefix = r"(\bvariables\.|\s|\bvar\s+)"
    regex = regex_prefix + variable_name + r"\b\s*=\s*"
    assignments = view.find_all(regex, sublime.IGNORECASE)
    for r in reversed(assignments):
        if r.begin() < position:
            # check for local var assignment
            # and ensure it is in the same function body
            if view.substr(r).lower().startswith("var "):
                function_region = get_current_function_body(view, r.end(), False)
                if not function_region or not function_region.contains(position):
                    continue
            return r
    return None


def get_verified_path(root_path, rel_path):
    """
    Given a valid root path and an unverified relative path out from that root
    path, searches to see if the full path exists. This search is case insensitive,
    but the returned relative path is cased accurately if it is found.
    returns a tuple of (rel_path, exists)
    """
    normalized_root_path = normalize_path(root_path)
    rel_path_elements = normalize_path(rel_path).split("/")
    verified_path_elements = []

    for elem in rel_path_elements:
        dir_map = {
            f.lower(): f
            for f in os.listdir(
                normalized_root_path + "/" + "/".join(verified_path_elements)
            )
        }
        if elem.lower() not in dir_map:
            return rel_path, False
        verified_path_elements.append(dir_map[elem.lower()])

    return "/".join(verified_path_elements), True
