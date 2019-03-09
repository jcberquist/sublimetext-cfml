import sublime
from collections import namedtuple
from .. import utils
from .delimited_scopes import DELIMITED_SCOPE_LIST

Block = namedtuple(
    "Block", "block_type, indent_pt, start_to_char, char_to_end, end_to_char"
)
BLOCK_START_SELECTOR = "punctuation.section.block.begin.cfml"
BLOCK_END_SELECTOR = "punctuation.section.block.end.cfml"
GROUP_SELECTOR = "meta.group, meta.function.parameters"


def format_blocks(cfml_format):
    blocks = cfml_format.find_by_nested_selector("meta.block.cfml")
    blocks.extend(cfml_format.find_by_nested_selector("meta.function.body.cfml"))

    groups = cfml_format.find_by_nested_selector("meta.group")
    groups.extend(cfml_format.find_by_nested_selector("meta.function.parameters"))
    groups = {r.end(): r.begin() for r in groups}

    substitutions = []

    for block_region in blocks:
        if not is_full_block(cfml_format, block_region):
            continue

        block = parse_block(cfml_format, block_region, groups)
        indent_column = cfml_format.line_indent_column(block.indent_pt)
        indent_str = cfml_format.indent_to_column(indent_column)
        sub_indent_str = cfml_format.indent_to_column(
            indent_column + cfml_format.tab_size
        )
        deindent_col = indent_column - cfml_format.tab_size
        if deindent_col < 0:
            deindent_col = 0

        # is this block empty
        if block.start_to_char.end() == block.char_to_end.end():
            empty_spacing = cfml_format.get_setting(
                "blocks.empty_spacing", block.block_type
            )
            if empty_spacing == "compact":
                substitutions.append((block.start_to_char, ""))
            elif empty_spacing == "spaced":
                substitutions.append((block.start_to_char, " "))
            elif empty_spacing == "newline":
                rep_str = "\n" + indent_str
                substitutions.append((block.start_to_char, rep_str))
            elif empty_spacing == "emptyline":
                rep_str = "\n\n" + indent_str
                substitutions.append((block.start_to_char, rep_str))
        else:
            # block start
            start_spacing = cfml_format.get_setting(
                "blocks.start_spacing", block.block_type
            )
            if start_spacing is not None and start_spacing in ["newline", "emptyline"]:
                space_str = "\n" + sub_indent_str
                if start_spacing == "emptyline":
                    space_str = "\n" + space_str
                substitutions.append((block.start_to_char, space_str))
            # block end
            end_spacing = cfml_format.get_setting(
                "blocks.end_spacing", block.block_type
            )
            if end_spacing is not None and end_spacing in ["newline", "emptyline"]:
                space_str = "\n" + indent_str
                if end_spacing == "emptyline":
                    space_str = "\n" + space_str
                substitutions.append((block.char_to_end, space_str))

        after_block_spacing = cfml_format.get_setting(
            "blocks.after_block_spacing", block.block_type
        )
        if after_block_spacing is None or after_block_spacing not in [
            "newline",
            "emptyline",
        ]:
            continue

        # after block spacing has to be ignored for keywords that follow block
        # e.g. `} else` or `} while`
        after_block_keyword = get_keyword(cfml_format, block.end_to_char.end())
        if after_block_keyword and after_block_keyword in [
            "else",
            "elseif",
            "while",
            "catch",
        ]:
            continue

        # after block spacing ignored inside delimited scopes
        if cfml_format.view.match_selector(
            block_region.begin(), ",".join(DELIMITED_SCOPE_LIST)
        ):
            continue

        # after block spacing ignored if followed by block end
        if is_block_end(cfml_format, block.end_to_char.end()):
            continue

        space_str = "\n" + indent_str
        if after_block_spacing == "emptyline":
            space_str = "\n" + space_str

        substitutions.append((block.end_to_char, space_str))

    return substitutions


def parse_block(cfml_format, block_region, groups):
    # need to find char pt from which to calc indent
    prev_char_pt = utils.get_previous_character(cfml_format.view, block_region.begin())

    if prev_char_pt + 1 in groups:
        prev_char_pt = utils.get_previous_character(
            cfml_format.view, groups[prev_char_pt + 1]
        )

    block_type = get_block_type(cfml_format, prev_char_pt)

    indent_pt = prev_char_pt if block_type != "anonymous" else block_region.begin()

    block_str = cfml_format.view.substr(block_region)[1:-1]
    first_block_char = (
        block_region.begin() + 1 + (len(block_str) - len(block_str.lstrip()))
    )
    start_to_char = sublime.Region(block_region.begin() + 1, first_block_char)

    last_block_char = (
        block_region.end() - 1 - (len(block_str) - len(block_str.rstrip()))
    )
    char_to_end = sublime.Region(last_block_char, block_region.end() - 1)

    after_block_char = utils.get_next_character(cfml_format.view, block_region.end())
    end_to_char = sublime.Region(block_region.end(), after_block_char)

    return Block(block_type, indent_pt, start_to_char, char_to_end, end_to_char)


def is_full_block(cfml_format, block_region):
    start_scope_name = cfml_format.view.scope_name(block_region.begin()).strip()
    end_scope_name = cfml_format.view.scope_name(block_region.end() - 1).strip()
    start_scope_parts = start_scope_name.split(" ")

    if start_scope_parts[-1] != BLOCK_START_SELECTOR:
        return False

    target_end_scope = " ".join(start_scope_parts[:-1]) + " " + BLOCK_END_SELECTOR
    if target_end_scope != end_scope_name:
        return False

    return True


def is_block_end(cfml_format, pt):
    return cfml_format.view.scope_name(pt).strip().endswith(BLOCK_END_SELECTOR)


def get_group_start(cfml_format, group_end_pt):
    pt = group_end_pt
    scope_name = cfml_format.view.scope_name(group_end_pt)
    end_scope_parts = scope_name.split(" ")
    base_scope = " ".join(end_scope_parts[:-2]) + " "
    start_scope = base_scope + end_scope_parts[-2].replace("end", "begin") + " "

    while scope_name != start_scope:
        pt -= 1
        scope_name = cfml_format.view.scope_name(pt)

    return pt


def get_block_type(cfml_format, pt):
    if cfml_format.view.match_selector(
        pt, "entity.name.function,storage.type.function"
    ):
        return "function"
    keyword = get_keyword(cfml_format, pt)
    return keyword if keyword else "anonymous"


def get_keyword(cfml_format, pt):
    if cfml_format.view.match_selector(pt, "keyword.control"):
        keyword = cfml_format.view.substr(cfml_format.view.word(pt))
        if keyword == "else" and cfml_format.view.match_selector(
            pt + 4, "keyword.control"
        ):
            keyword = "elseif"
        return keyword
    return None
