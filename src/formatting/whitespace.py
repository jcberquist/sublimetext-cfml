import sublime
from .. import utils
from .delimited_scopes import DELIMITED_SCOPES

OPERATOR_SELECTOR = "source.cfml.script keyword.operator -source.sql"
WHITESPACE_CONTAINER_START = ",".join([DELIMITED_SCOPES[k]["start"] for k in DELIMITED_SCOPES])
WHITESPACE_CONTAINER_END = ",".join([DELIMITED_SCOPES[k]["end"] for k in DELIMITED_SCOPES])


def format_whitespace(cfml_format, delimited_scope_command=False):
    regions = []
    regions.extend(format_operators(cfml_format))
    regions.extend(format_parentheses(cfml_format))
    regions.extend(format_brackets(cfml_format))
    regions.extend(format_struct_key_values(cfml_format))
    regions.extend(format_for_semicolons(cfml_format))
    if not delimited_scope_command:
        regions.extend(format_delimited_scopes(cfml_format))
    return regions


def format_operators(cfml_format):
    binary_operators = cfml_format.get_setting("binary_operators", default={})
    padding = binary_operators.get("padding")
    padding_strip_newlines = binary_operators.get("padding_strip_newlines", False)
    format_assignment_operator = binary_operators.get("format_assignment_operator", False)
    substitutions = []

    if padding is None or padding not in ["spaced", "compact"]:
        return substitutions

    space_str = " " if padding == "spaced" else ""

    operators = cfml_format.find_by_selector(OPERATOR_SELECTOR)

    for r in operators:
        operator = cfml_format.view.substr(r)
        if (
            operator in ["++", "--", "!", "!!"]
            or
            (operator == "=" and not format_assignment_operator)
        ):
            continue

        prev_pt = utils.get_previous_character(cfml_format.view, r.begin())
        if not cfml_format.view.match_selector(prev_pt, WHITESPACE_CONTAINER_START):
            replacement_region = sublime.Region(prev_pt + 1, r.begin())
            if padding_strip_newlines:
                substitutions.append((replacement_region, space_str))
            else:
                prev_str = cfml_format.view.substr(replacement_region)
                if "\n" not in prev_str:
                    substitutions.append((replacement_region, space_str))

        next_pt = utils.get_next_character(cfml_format.view, r.end())
        if not cfml_format.view.match_selector(next_pt, WHITESPACE_CONTAINER_END):
            replacement_region = sublime.Region(r.end(), next_pt)
            if (
                operator in ["+", "-"]
                and cfml_format.view.match_selector(prev_pt, OPERATOR_SELECTOR)
                and cfml_format.view.match_selector(next_pt, "constant.numeric.cfml")
            ):
                substitutions.append((replacement_region, ""))
            elif padding_strip_newlines:
                substitutions.append((replacement_region, space_str))
            else:
                next_str = cfml_format.view.substr(replacement_region)
                if "\n" not in next_str:
                    substitutions.append((replacement_region, space_str))

    return substitutions


def format_parentheses(cfml_format):
    parentheses = cfml_format.get_setting("parentheses", default={})
    padding = parentheses.get("padding")
    padding_strip_newlines = parentheses.get("padding_strip_newlines", False)
    substitutions = []

    if padding is None or padding not in ["spaced", "compact"]:
        return substitutions

    groups = cfml_format.find_by_nested_selector("meta.group.cfml")

    for r in groups:
        # keyword groups are formatted separately
        prev_pt = utils.get_previous_character(cfml_format.view, r.begin())
        if cfml_format.view.match_selector(prev_pt, "keyword.control"):
            continue
        substitutions.extend(cfml_format.inner_scope_spacing(r, None, padding, padding_strip_newlines))

    return substitutions


def format_brackets(cfml_format):
    brackets = cfml_format.get_setting("brackets")

    if brackets is None:
        return []

    padding_strip_newlines = brackets.get("padding_strip_newlines", False)
    space_str = " " if brackets.get("padding") == "spaced" else ""

    bracket_starts = cfml_format.find_by_selector("meta.brackets.cfml punctuation.section.brackets.begin.cfml")
    bracket_ends = cfml_format.find_by_selector("meta.brackets.cfml punctuation.section.brackets.end.cfml")
    substitutions = []

    for r in bracket_starts:
        first_char = utils.get_next_character(cfml_format.view, r.begin() + 1)
        bracket_to_char = sublime.Region(r.begin() + 1, first_char)
        if padding_strip_newlines or "\n" not in cfml_format.view.substr(bracket_to_char):
            substitutions.append((bracket_to_char, space_str))

        prev_char = utils.get_previous_character(cfml_format.view, r.begin())
        char_to_bracket = sublime.Region(prev_char + 1, r.begin())
        if char_to_bracket.size() > 0:
            substitutions.append((char_to_bracket, ""))

    for r in bracket_ends:
        prev_char = utils.get_previous_character(cfml_format.view, r.begin())
        char_to_bracket_end = sublime.Region(prev_char + 1, r.end())
        if padding_strip_newlines or "\n" not in cfml_format.view.substr(char_to_bracket_end):
            substitutions.append((char_to_bracket_end, (space_str + ']') * r.size()))

    return substitutions


def format_struct_key_values(cfml_format):
    struct = cfml_format.get_setting("struct", default={})
    substitutions = []

    key_value_selector = "meta.struct-literal.cfml punctuation.separator.key-value.cfml "
    key_value_colon = struct.get("key_value_colon", None)
    key_value_equals = struct.get("key_value_equals", None)
    key_values_separators = cfml_format.find_by_selector(key_value_selector)
    for r in key_values_separators:
        if not cfml_format.view.scope_name(r.begin()).endswith(key_value_selector):
            continue

        separator = cfml_format.view.substr(r)
        separator_setting = key_value_equals if separator == "=" else key_value_colon
        if separator_setting is None or separator_setting not in ["spaced", "compact"]:
            continue

        space_str = " " if separator_setting == "spaced" else ""

        prev_pt = utils.get_previous_character(cfml_format.view, r.begin())
        if not cfml_format.view.match_selector(prev_pt, WHITESPACE_CONTAINER_START):
            prev_space_str = space_str if separator == "=" else ""
            substitutions.append((sublime.Region(prev_pt + 1, r.begin()), prev_space_str))

        next_pt = utils.get_next_character(cfml_format.view, r.end())
        if not cfml_format.view.match_selector(next_pt, WHITESPACE_CONTAINER_END):
            substitutions.append((sublime.Region(r.end(), next_pt), space_str))

    return substitutions


def format_for_semicolons(cfml_format):
    for_loop_semicolons = cfml_format.get_setting("for_loop_semicolons", default={})
    padding = for_loop_semicolons.get("padding")
    substitutions = []

    if padding is None or padding not in ["spaced", "compact"]:
        return substitutions

    selector = "meta.for.cfml meta.group.cfml punctuation.terminator.statement.cfml"
    space_str = " " if padding == "spaced" else ""
    semicolons = cfml_format.find_by_selector(selector)
    for r in semicolons:
        for pt in range(r.begin(), r.end()):
            next_pt = utils.get_next_character(cfml_format.view, pt + 1)
            if not cfml_format.view.match_selector(next_pt, WHITESPACE_CONTAINER_END):
                substitutions.append((sublime.Region(pt + 1, next_pt), space_str))

    return substitutions


def format_delimited_scopes(cfml_format):
    substitutions = []
    for scope in DELIMITED_SCOPES:
        settings = cfml_format.get_setting(scope, default={})
        substitutions.extend(format_delimited_scope(cfml_format, settings, DELIMITED_SCOPES[scope]))
    return substitutions


def format_delimited_scope(cfml_format, scope_settings, scope):
    substitutions = []

    separators = cfml_format.find_by_selector(scope["separator"])
    for r in separators:
        prev_pt = utils.get_previous_character(cfml_format.view, r.begin())
        if not cfml_format.view.match_selector(prev_pt, WHITESPACE_CONTAINER_START):
            replacement_region = sublime.Region(prev_pt + 1, r.begin())
            prev_str = cfml_format.view.substr(replacement_region)
            if "\n" not in prev_str:
                substitutions.append((replacement_region, ""))

        after_comma_spacing = scope_settings.get("after_comma_spacing", None)
        if after_comma_spacing and after_comma_spacing in ["spaced", "compact"]:
            space_str = " " if after_comma_spacing == "spaced" else ""
            next_pt = utils.get_next_character(cfml_format.view, r.end())
            if not cfml_format.view.match_selector(next_pt, WHITESPACE_CONTAINER_END):
                replacement_region = sublime.Region(r.end(), next_pt)
                next_str = cfml_format.view.substr(replacement_region)
                if "\n" not in next_str:
                    substitutions.append((replacement_region, space_str))

    regions = cfml_format.find_by_nested_selector(scope["scope"])
    for r in regions:
        # do we have the full scope?
        if cfml_format.is_full_scope(r, scope["start"], scope["end"]):
            empty_spacing = scope_settings.get("empty_spacing", None)
            padding_inside = scope_settings.get("padding_inside", None)
            substitutions.extend(cfml_format.inner_scope_spacing(r, empty_spacing, padding_inside))

    return substitutions
