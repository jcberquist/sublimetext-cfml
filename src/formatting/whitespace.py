import sublime
import re
from .. import utils
from .delimited_scopes import DELIMITED_SCOPES


OPERATOR_SELECTOR = "source.cfml.script keyword.operator -source.sql"
WHITESPACE_CONTAINER_START = ",".join(
    [DELIMITED_SCOPES[k]["start"] for k in DELIMITED_SCOPES]
)
WHITESPACE_CONTAINER_END = ",".join(
    [DELIMITED_SCOPES[k]["end"] for k in DELIMITED_SCOPES]
)
WORD_OPERATOR = re.compile("[a-z][a-z ]*[a-z]$", re.IGNORECASE)


def format_whitespace(cfml_format, delimited_scope_command=False):
    regions = []
    regions.extend(format_operators(cfml_format))
    regions.extend(format_parentheses(cfml_format))
    regions.extend(format_brackets(cfml_format))
    regions.extend(format_struct_key_values(cfml_format))
    regions.extend(format_for_semicolons(cfml_format))
    return regions


def format_operators(cfml_format):
    padding = cfml_format.get_setting("binary_operators.padding")
    padding_strip_newlines = cfml_format.get_setting(
        "binary_operators.padding_strip_newlines", default=False
    )
    format_assignment_operator = cfml_format.get_setting(
        "binary_operators.format_assignment_operator", default=False
    )
    substitutions = []

    if padding is None or padding not in ["spaced", "compact"]:
        return substitutions

    operators = cfml_format.find_by_selector(OPERATOR_SELECTOR)

    for r in operators:
        scope_name = cfml_format.view.scope_name(r.begin())
        operator = cfml_format.view.substr(r)
        is_word = re.match(WORD_OPERATOR, operator) is not None

        if (
            "keyword.operator.assignment" in scope_name
            and not format_assignment_operator
        ):
            continue

        space_str = ""
        if is_word or (
            padding == "spaced"
            and (".binary." in scope_name or ".ternary." in scope_name)
        ):
            space_str = " "

        if (
            ".binary." in scope_name
            or ".ternary." in scope_name
            or ".postfix." in scope_name
        ):
            prev_pt = utils.get_previous_character(cfml_format.view, r.begin())
            if not cfml_format.view.match_selector(prev_pt, WHITESPACE_CONTAINER_START):
                replacement_region = sublime.Region(prev_pt + 1, r.begin())
                if padding_strip_newlines:
                    substitutions.append((replacement_region, space_str))
                else:
                    prev_str = cfml_format.view.substr(replacement_region)
                    if "\n" not in prev_str:
                        substitutions.append((replacement_region, space_str))

        if (
            ".binary." in scope_name
            or ".ternary." in scope_name
            or ".prefix." in scope_name
        ):
            next_pt = utils.get_next_character(cfml_format.view, r.end())
            if not cfml_format.view.match_selector(next_pt, WHITESPACE_CONTAINER_END):
                replacement_region = sublime.Region(r.end(), next_pt)
                if padding_strip_newlines:
                    substitutions.append((replacement_region, space_str))
                else:
                    next_str = cfml_format.view.substr(replacement_region)
                    if "\n" not in next_str:
                        substitutions.append((replacement_region, space_str))

    return substitutions


def format_parentheses(cfml_format):
    padding = cfml_format.get_setting("parentheses.padding")
    padding_strip_newlines = cfml_format.get_setting(
        "parentheses.padding_strip_newlines", default=False
    )
    substitutions = []

    if padding is None or padding not in ["spaced", "compact"]:
        return substitutions

    groups = cfml_format.find_by_nested_selector("meta.group.cfml")

    for r in groups:
        # keyword groups are formatted separately
        prev_pt = utils.get_previous_character(cfml_format.view, r.begin())
        if cfml_format.view.match_selector(prev_pt, "keyword.control"):
            continue
        substitutions.extend(
            cfml_format.inner_scope_spacing(r, None, padding, padding_strip_newlines)
        )

    return substitutions


def format_brackets(cfml_format):
    padding_strip_newlines = cfml_format.get_setting(
        "brackets.padding_strip_newlines", default=False
    )
    space_str = " " if cfml_format.get_setting("brackets.padding") == "spaced" else ""

    bracket_starts = cfml_format.find_by_selector(
        "meta.brackets.cfml punctuation.section.brackets.begin.cfml"
    )
    bracket_ends = cfml_format.find_by_selector(
        "meta.brackets.cfml punctuation.section.brackets.end.cfml"
    )
    substitutions = []

    for r in bracket_starts:
        first_char = utils.get_next_character(cfml_format.view, r.begin() + 1)
        bracket_to_char = sublime.Region(r.begin() + 1, first_char)
        if padding_strip_newlines or "\n" not in cfml_format.view.substr(
            bracket_to_char
        ):
            substitutions.append((bracket_to_char, space_str))

        prev_char = utils.get_previous_character(cfml_format.view, r.begin())
        char_to_bracket = sublime.Region(prev_char + 1, r.begin())
        if char_to_bracket.size() > 0:
            substitutions.append((char_to_bracket, ""))

    for r in bracket_ends:
        prev_char = utils.get_previous_character(cfml_format.view, r.begin())
        char_to_bracket_end = sublime.Region(prev_char + 1, r.end())
        if padding_strip_newlines or "\n" not in cfml_format.view.substr(
            char_to_bracket_end
        ):
            substitutions.append((char_to_bracket_end, (space_str + "]") * r.size()))

    return substitutions


def format_struct_key_values(cfml_format):
    substitutions = []

    key_value_selector = (
        "meta.struct-literal.cfml punctuation.separator.key-value.cfml "
    )
    key_value_colon = cfml_format.get_setting("struct.key_value_colon")
    key_value_equals = cfml_format.get_setting("struct.key_value_equals")
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
            substitutions.append(
                (sublime.Region(prev_pt + 1, r.begin()), prev_space_str)
            )

        next_pt = utils.get_next_character(cfml_format.view, r.end())
        if not cfml_format.view.match_selector(next_pt, WHITESPACE_CONTAINER_END):
            substitutions.append((sublime.Region(r.end(), next_pt), space_str))

    return substitutions


def format_for_semicolons(cfml_format):
    padding = cfml_format.get_setting("for_loop_semicolons.padding")
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
