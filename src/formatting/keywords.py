import sublime
from .. import utils

KEYWORD_SELECTOR = "source.cfml.script keyword.control"
GROUP_SELECTOR = "meta.group.cfml"
GROUP_START_SELECTOR = "meta.group.cfml punctuation.section.group.begin.cfml"
BLOCK_START_SELECTOR = "meta.block.cfml punctuation.section.block.begin.cfml"
BLOCK_END_SELECTOR = "meta.block.cfml punctuation.section.block.end.cfml"
WHILE_SELECTOR = " meta.while.cfml"
PREVIOUS_BLOCK_SCOPES = {
    "while": "meta.do-while.cfml",
    "catch": "meta.try.cfml",
    "else": "meta.conditional.cfml",
    "elseif": "meta.conditional.cfml",
}
FUNCTION_SELECTOR = (
    "source.cfml.script meta.function.declaration.cfml storage.type.function.cfml"
)
FUNCTION_NAME_SELECTOR = (
    "source.cfml.script meta.function.declaration.cfml entity.name.function.cfml"
)
FUNCTION_GROUP_SELECTOR = "source.cfml.script meta.function.parameters.cfml punctuation.section.parameters.begin.cfml"
FUNCTION_GROUP_END_SELECTOR = "source.cfml.script meta.function.parameters.cfml punctuation.section.parameters.end.cfml"
FUNCTION_BLOCK_START_SELECTOR = (
    "source.cfml.script meta.function.body.cfml punctuation.section.block.begin.cfml"
)


def format_keywords(cfml_format):
    keywords = cfml_format.find_by_selector(KEYWORD_SELECTOR)
    keyword_groups = cfml_format.find_by_selector(GROUP_SELECTOR)

    group_index = 0
    substitutions = []

    for r in keywords:
        keyword = cfml_format.view.substr(r).replace(" ", "")

        # previous code pt
        previous_char_point = utils.get_previous_character(cfml_format.view, r.begin())
        if not cfml_format.view.match_selector(previous_char_point, "comment"):

            if keyword in ["else", "elseif", "while", "catch"]:
                to_keyword_spacing = cfml_format.get_setting(
                    "keywords.block_to_keyword_spacing", keyword
                )
                if to_keyword_spacing in ["newline", "spaced", "compact"]:
                    previous_scope_name = cfml_format.view.scope_name(
                        previous_char_point
                    )
                    if previous_scope_name.strip().endswith(
                        PREVIOUS_BLOCK_SCOPES[keyword] + " " + BLOCK_END_SELECTOR
                    ):
                        replacement_region = sublime.Region(
                            previous_char_point + 1, r.begin()
                        )
                        replacement_str = get_spacing_string(
                            cfml_format, previous_char_point, to_keyword_spacing
                        )
                        substitutions.append((replacement_region, replacement_str))
            else:
                to_keyword_spacing = cfml_format.get_setting(
                    "keywords.to_keyword_spacing", keyword
                )
                if to_keyword_spacing in ["newline", "emptyline"]:
                    replacement_region = sublime.Region(
                        previous_char_point + 1, r.begin()
                    )
                    replacement_str = get_spacing_string(
                        cfml_format, r.begin(), to_keyword_spacing
                    )
                    substitutions.append((replacement_region, replacement_str))

        # quick check on else if to normalize to single space between else and if
        if keyword == "elseif" and r.size() != 7:
            replacement_region = sublime.Region(r.begin() + 4, r.end() - 2)
            replacement_str = " "
            substitutions.append((replacement_region, replacement_str))

        prev_char_pt = r.end()
        next_char_pt = utils.get_next_character(cfml_format.view, r.end())

        # could be a group
        has_group = False
        if cfml_format.view.match_selector(next_char_pt, GROUP_START_SELECTOR):
            has_group = True
            spacing_to_group = cfml_format.get_setting(
                "keywords.spacing_to_group", keyword
            )
            if spacing_to_group is not None and spacing_to_group in [
                "spaced",
                "compact",
            ]:
                keyword_to_group = sublime.Region(prev_char_pt, next_char_pt)
                replacement_str = " " if spacing_to_group == "spaced" else ""
                substitutions.append((keyword_to_group, replacement_str))

            # find the corresponding group
            try:
                while next_char_pt > keyword_groups[group_index].begin():
                    group_index += 1
            except Exception:
                print("CFML: Unable to find group while performing keyword format.")
                print(r, keyword)

            empty_group_spacing = cfml_format.get_setting(
                "keywords.empty_group_spacing", keyword
            )
            padding_inside_group = cfml_format.get_setting(
                "keywords.padding_inside_group", keyword
            )
            padding_strip_newlines = cfml_format.get_setting(
                "keywords.padding_strip_newlines", keyword, False
            )
            substitutions.extend(
                cfml_format.inner_scope_spacing(
                    keyword_groups[group_index],
                    empty_group_spacing,
                    padding_inside_group,
                    padding_strip_newlines,
                )
            )
            prev_char_pt = keyword_groups[group_index].end()
            next_char_pt = utils.get_next_character(cfml_format.view, prev_char_pt)

        # now check for block
        to_next_char = sublime.Region(prev_char_pt, next_char_pt)
        block_selector = BLOCK_START_SELECTOR
        if keyword == "while":
            block_selector = WHILE_SELECTOR + " " + block_selector
        next_char_is_block = cfml_format.view.match_selector(
            next_char_pt, block_selector
        )

        if not next_char_is_block:
            next_char = cfml_format.view.substr(next_char_pt)
            if to_next_char.size() != 1 and next_char not in [";", ":"]:
                replacement_str = " "
                substitutions.append((to_next_char, replacement_str))
            elif to_next_char.size() > 0 and next_char in [";", ":"]:
                replacement_str = ""
                substitutions.append((to_next_char, replacement_str))
            continue

        setting_key = "group_to_block_spacing" if has_group else "spacing_to_block"
        to_block_spacing = cfml_format.get_setting("keywords." + setting_key, keyword)
        if to_block_spacing and to_block_spacing in ["newline", "spaced", "compact"]:
            replacement_str = get_spacing_string(
                cfml_format, prev_char_pt, to_block_spacing
            )
            substitutions.append((to_next_char, replacement_str))

    substitutions.extend(format_function_keywords(cfml_format))
    return substitutions


def format_function_keywords(cfml_format):
    substitutions = []

    spacing_to_group = cfml_format.get_setting("function_declaration.spacing_to_group")
    if spacing_to_group and spacing_to_group in ["spaced", "compact"]:
        function_keywords = cfml_format.find_by_selector(
            FUNCTION_SELECTOR + "," + FUNCTION_NAME_SELECTOR
        )

        for r in function_keywords:
            next_char_pt = utils.get_next_character(cfml_format.view, r.end())
            if cfml_format.view.match_selector(next_char_pt, FUNCTION_GROUP_SELECTOR):
                keyword_to_group = sublime.Region(r.end(), next_char_pt)
                replacement_str = " " if spacing_to_group == "spaced" else ""
                substitutions.append((keyword_to_group, replacement_str))

    group_to_block_spacing = cfml_format.get_setting(
        "function_declaration.group_to_block_spacing"
    )
    if group_to_block_spacing and group_to_block_spacing in [
        "newline",
        "spaced",
        "compact",
    ]:
        param_end_regions = cfml_format.find_by_selector(FUNCTION_GROUP_END_SELECTOR)

        for r in param_end_regions:
            next_char_pt = utils.get_next_character(cfml_format.view, r.end())
            if cfml_format.view.match_selector(
                next_char_pt, FUNCTION_BLOCK_START_SELECTOR
            ):
                group_to_block = sublime.Region(r.end(), next_char_pt)
                replacement_str = get_spacing_string(
                    cfml_format, r.end(), group_to_block_spacing
                )
                substitutions.append((group_to_block, replacement_str))

    return substitutions


def get_spacing_string(cfml_format, pt, setting):
    if setting == "spaced":
        return " "
    elif setting == "compact":
        return ""
    elif setting == "newline":
        line_indent = cfml_format.line_indent_column(pt)
        return "\n" + cfml_format.indent_to_column(line_indent)
    elif setting == "emptyline":
        line_indent = cfml_format.line_indent_column(pt)
        return "\n\n" + cfml_format.indent_to_column(line_indent)
