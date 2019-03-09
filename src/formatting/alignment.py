import sublime


start_indent_selectors = [
    "punctuation.section.block.begin.cfml",
    "punctuation.section.brackets.begin.cfml",
    "punctuation.section.parameters.begin.cfml",
    "punctuation.section.group.begin.cfml",
]

end_indent_selectors = [
    "punctuation.section.block.end.cfml",
    "punctuation.section.brackets.end.cfml",
    "punctuation.section.parameters.end.cfml",
    "punctuation.section.group.end.cfml",
]

non_script_selector = "embedding.cfml -source.cfml.script"

non_indent_selector = [
    "comment.block.cfml -punctuation.definition.comment.cfml",
    "meta.string -punctuation.definition.string.begin",
]

switch_block_end = "meta.switch.cfml meta.block.cfml punctuation.section.block.end.cfml"


def indent_region(cfml_format):
    start_indent_selector = ",".join(start_indent_selectors)
    end_indent_selector = ",".join(end_indent_selectors)
    accessor_selector = "punctuation.accessor.cfml"

    non_cfscript_regions = cfml_format.view.find_by_selector(non_script_selector)
    non_indent_regions = cfml_format.view.find_by_selector(
        ",".join(non_indent_selector)
    )
    non_cfscript_line_starts = set()
    non_indent_line_starts = set()

    for r in non_cfscript_regions:
        for l in cfml_format.view.split_by_newlines(r):
            non_cfscript_line_starts.add(l.begin())

    for r in non_indent_regions:
        for l in cfml_format.view.split_by_newlines(r):
            non_indent_line_starts.add(l.begin())

    lines = cfml_format.view.lines(cfml_format.region_to_format)
    base_indent_column = cfml_format.line_indent_column(lines[0].begin())

    indent_level = 0
    leading_comma_flag = False
    switch_case_flag = None
    replacements = []

    if lines[0].begin() < cfml_format.region_to_format.begin():
        first_line_str = cfml_format.view.substr(lines[0])
        first_line_stripped = first_line_str.rstrip()
        if first_line_stripped[-1] in ["{", "(", "["]:
            last_char_pt = lines[0].begin() + len(first_line_stripped) - 1
            if cfml_format.view.match_selector(last_char_pt, start_indent_selector):
                indent_level += 1
        lines = lines[1:]

    if len(lines) > 0 and lines[-1].end() > cfml_format.region_to_format.end():
        lines = lines[:-1]

    if len(lines) == 0:
        return []

    for l in lines:
        full_line_str = cfml_format.view.substr(l)
        stripped_line_str = full_line_str.strip()

        if l.begin() in non_cfscript_line_starts:
            base_indent_column = cfml_format.line_indent_column(l.begin())

        if len(stripped_line_str) == 0:
            replacements.append(stripped_line_str)
            continue

        first_line_char = stripped_line_str[0]

        if first_line_char in ["}", ")", "]", ",", "."]:
            first_char_pt = l.begin() + full_line_str.index(first_line_char)

        if first_line_char in ["}", ")", "]"] and cfml_format.view.match_selector(
            first_char_pt, end_indent_selector
        ):
            indent_level -= 1

        if first_line_char == "}" and switch_case_flag == "case_block":
            scope_name = cfml_format.view.scope_name(first_char_pt)
            if scope_name.strip().endswith(switch_block_end):
                switch_case_flag = None
                indent_level -= 1

        if stripped_line_str[-1] == ":":
            last_char_pt = l.begin() + len(full_line_str.rstrip()) - 1
            scope_name = cfml_format.view.scope_name(last_char_pt)
            if scope_name.strip().endswith(
                "meta.switch.cfml meta.block.cfml punctuation.separator.cfml"
            ):
                if switch_case_flag == "case_block":
                    indent_level -= 1
                switch_case_flag = "case_start"

        indent_columns = base_indent_column + (cfml_format.tab_size * indent_level)

        # leading comma alignment
        if first_line_char == "," and cfml_format.view.match_selector(
            first_char_pt, "punctuation.separator"
        ):
            if not leading_comma_flag:
                # move previous line over to align
                offset = 2 if stripped_line_str[1] == " " else 1
                replacements[-1] = (
                    cfml_format.indent_to_column(indent_columns + offset)
                    + replacements[-1].strip()
                )
                leading_comma_flag = True
        else:
            leading_comma_flag = False

        # lines that start with a method call get an extra indent
        if first_line_char == "." and cfml_format.view.match_selector(
            first_char_pt, accessor_selector
        ):
            indent_columns += cfml_format.tab_size

        indented_line = cfml_format.indent_to_column(indent_columns) + stripped_line_str

        if l.begin() in non_cfscript_line_starts or l.begin() in non_indent_line_starts:
            replacements.append(full_line_str)
        else:
            replacements.append(indented_line)

        if stripped_line_str[-1] in ["{", "(", "["]:
            last_char_pt = l.begin() + len(full_line_str.rstrip()) - 1
            if cfml_format.view.match_selector(last_char_pt, start_indent_selector):
                indent_level += 1

        if switch_case_flag == "case_start":
            indent_level += 1
            switch_case_flag = "case_block"

    replacement_str = "\n".join(replacements)

    return [(sublime.Region(lines[0].begin(), lines[-1].end()), replacement_str)]


def align_assignment_operators(cfml_format):
    if not cfml_format.get_setting("binary_operators.format_assignment_operator"):
        return []

    if not cfml_format.get_setting("binary_operators.align_sequential_assignments"):
        return []

    selector = "keyword.operator.assignment.binary.cfml"
    operators = cfml_format.find_by_selector(selector)

    def is_in_seq(seq, assignment_tuple):
        if len(seq) == 0:
            return False

        prev_op_region, prev_op_scope, prev_line_region = seq[-1]
        op_region, op_scope, line_region = assignment_tuple

        if prev_line_region.end() != line_region.begin() - 1:
            return False

        if prev_op_scope != op_scope:
            return False

        return True

    def max_start(seq):
        offsets = [
            op_region.begin() - line_region.begin()
            for op_region, op_scope, line_region in seq
        ]
        return max(offsets)

    def align_line(op_region, op_scope, line_region, offset):
        line_start = cfml_format.view.substr(
            sublime.Region(line_region.begin(), op_region.begin())
        ).rstrip()
        indent_needed = offset - len(line_start)
        align_region = sublime.Region(line_region.begin(), op_region.end())
        align_string = line_start + cfml_format.indent_to_column(indent_needed) + "="
        return align_region, align_string

    def align_sequence(seq):
        if len(seq) < 2:
            return []
        seq_replacements = []
        offset = max_start(seq)
        # offset += offset % cfml_format.tab_size
        for op_region, op_scope, line_region in seq:
            seq_replacements.append(
                align_line(op_region, op_scope, line_region, offset)
            )
        return seq_replacements

    replacements = []
    operator_sequence = []

    for op_region in operators:
        op_scope = cfml_format.view.scope_name(op_region.begin())
        line = cfml_format.view.line(op_region)
        assignment_tuple = op_region, op_scope, line

        if not is_in_seq(operator_sequence, assignment_tuple):
            replacements.extend(align_sequence(operator_sequence))
            operator_sequence = []

        operator_sequence.append(assignment_tuple)

    if len(operator_sequence) > 0:
        replacements.extend(align_sequence(operator_sequence))

    return replacements
