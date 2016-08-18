import sublime
from collections import namedtuple

DELIMITED_SCOPES = {
    "struct": {
        "scope": "meta.struct-literal.cfml",
        "start": "punctuation.definition.block.begin.cfml",
        "end": "punctuation.definition.block.end.cfml",
        "separator": "punctuation.separator.struct-literal.cfml"
    },
    "array": {
        "scope": "meta.array-literal.cfml",
        "start": "punctuation.definition.brackets.begin.cfml",
        "end": "punctuation.definition.brackets.end.cfml",
        "separator": "punctuation.separator.array-literal.cfml"
    },
    "function_declaration": {
        "scope": "meta.function.parameters.cfml",
        "start": "punctuation.definition.parameters.begin.cfml",
        "end": "punctuation.definition.parameters.end.cfml",
        "separator": "punctuation.separator.function.cfml"
    },
    "function_call": {
        "scope": "meta.function-call.parameters",
        "start": "punctuation.definition.group.begin.cfml",
        "end": "punctuation.definition.group.end.cfml",
        "separator": "punctuation.separator.function-call"
    }
}

DELIMITED_SCOPE_LIST = [DELIMITED_SCOPES[k]["scope"] for k in DELIMITED_SCOPES]

DelimitedScope = namedtuple(
    "DelimitedScope",
    "scope_type, scope_region, inline_string, has_multi_element_break, elements"
)


def format_delimited_scopes(cfml_format):
    depth = scope_depth(cfml_format.view, cfml_format.region_to_format.begin() - 1)
    scope_list = [e["scope"] + " " + e["start"] for k, e in DELIMITED_SCOPES.items()]

    depth += 1

    region_starts = []
    for r in cfml_format.find_by_selector(",".join(scope_list)):
        for pt in range(r.begin(), r.end()):
            scope_name = cfml_format.view.scope_name(pt).rstrip()
            if (
              determine_scope_type(scope_name.split(" ")) and
              scope_depth(cfml_format.view, pt) == depth
             ):
                region_starts.append(pt)
                break

    formatted_params = []
    for pt in region_starts:
        ds = parse_delimited_scope(cfml_format, pt)

        indent_column = cfml_format.line_indent_column(ds.scope_region.begin())
        ds_start_column = cfml_format.pt_column(ds.scope_region.begin())
        formatted_str = render_delimited_scope(cfml_format, ds, indent_column, ds_start_column)

        if cfml_format.view.substr(ds.scope_region) != formatted_str:
            formatted_params.append((ds.scope_region, formatted_str))

    return formatted_params


def determine_scope_type(scope_list):
    for scope_type in DELIMITED_SCOPES:
        if (
          scope_list[-2].startswith(DELIMITED_SCOPES[scope_type]["scope"]) and
          scope_list[-1] == DELIMITED_SCOPES[scope_type]["start"]
          ):
            return scope_type
    return None


def parse_delimited_scope(cfml_format, scope_pt):
    start_scope_list = cfml_format.view.scope_name(scope_pt).rstrip().split(' ')
    scope_type = determine_scope_type(start_scope_list)

    if not scope_type:
        print('NO MATCH', scope_pt, cfml_format.view.substr(scope_pt), cfml_format.view.scope_name(scope_pt))
        return

    base_scope = " ".join(start_scope_list[:-1])
    end_scope = base_scope + " " + DELIMITED_SCOPES[scope_type]["end"]
    delimiter_scope = base_scope + " " + DELIMITED_SCOPES[scope_type]["separator"]

    elements = []
    has_multi_element_break = False
    current_pt = start_pt = scope_pt + 1
    current_element = []

    while True:
        current_scope = cfml_format.view.scope_name(current_pt).rstrip()
        current_scope_parts = current_scope.split(" ")

        if current_scope == end_scope:
            if start_pt != current_pt:
                current_element.append(sublime.Region(start_pt, current_pt))
            elements.append(current_element)
            break

        elif current_scope.startswith(delimiter_scope):
            if start_pt != current_pt:
                current_element.append(sublime.Region(start_pt, current_pt))
            elements.append(current_element)
            current_element = []
            current_pt += 1
            start_pt = current_pt

        elif determine_scope_type(current_scope_parts):
            if start_pt != current_pt:
                current_element.append(sublime.Region(start_pt, current_pt))
            ds = parse_delimited_scope(cfml_format, current_pt)
            current_element.append(ds)
            if ds.has_multi_element_break:
                has_multi_element_break = True
            start_pt = current_pt = ds.scope_region.end()

        else:
            current_pt += 1

    element_count = cfml_format.get_setting(scope_type).get("multiline", {}).get("element_count")
    if element_count is not None and element_count >= 0 and len(elements) >= element_count:
        has_multi_element_break = True

    scope_region = sublime.Region(scope_pt, current_pt + 1)
    inline_string = render_delimited_scope_inline(cfml_format, scope_type, scope_region, elements)
    return DelimitedScope(scope_type, scope_region, inline_string, has_multi_element_break, elements)


def render_delimited_scope_inline(cfml_format, scope_type, scope_region, elements):

    def render_element(el):
        el_str = ""
        for part in el:
            if isinstance(part, DelimitedScope):
                el_str += part.inline_string
            else:
                el_str += cfml_format.view.substr(part)
        return el_str.strip()

    settings = cfml_format.get_setting(scope_type, default={})
    after_comma_spacing = settings.get("after_comma_spacing")
    separator = ", " if after_comma_spacing and after_comma_spacing == "spaced" else ","
    element_strs = [render_element(el) for el in elements]
    scope_string = separator.join(element_strs)

    padding_inside = settings.get("padding_inside", None)
    if padding_inside is not None and padding_inside == "spaced":
        scope_string = " " + scope_string + " "

    if scope_string.strip() == "":
        empty_spacing = settings.get("empty_spacing", None)
        if empty_spacing is not None and empty_spacing in ["compact", "spaced"]:
            scope_string = " " if empty_spacing == "spaced" else ""

    begin = cfml_format.view.substr(scope_region.begin())
    end = cfml_format.view.substr(scope_region.end() - 1)

    return begin + scope_string + end


def scope_depth(view, pt):
    depth = 0
    for scope_name in view.scope_name(pt).split(" "):
        if any(scope_name.startswith(item) for item in DELIMITED_SCOPE_LIST):
            depth += 1
    return depth


def is_multiline(settings, singleline_max_col, ds, ds_start_column):
    if len(ds.inline_string.replace(" ", "")) == 2:
        return False
    region_columns = len(ds.inline_string)
    region_end_col = ds_start_column + region_columns
    if (
        ds.has_multi_element_break
        or ds.inline_string.count("\n") > 0
        or (
            singleline_max_col is not None and singleline_max_col > 0 and
            region_end_col > singleline_max_col
        )
      ):
        return True
    return False


def render_ds_element(cfml_format, el, indent_column, ds_start_column):
    el_str = ""
    for part in el:
        if isinstance(part, DelimitedScope):
            txt_lines = el_str.split("\n")
            if len(txt_lines) > 1:
                last_start_column = cfml_format.text_columns(txt_lines[-1]) + 1
                last_indent_column = cfml_format.text_indent_columns(txt_lines[-1])
            else:
                last_start_column = ds_start_column + cfml_format.text_columns(el_str) + 1
                last_indent_column = indent_column

            el_str += render_delimited_scope(cfml_format, part, last_indent_column, last_start_column)
        else:
            el_str += cfml_format.view.substr(part)

    return el_str.strip()


def render_delimited_scope(cfml_format, ds, indent_column, ds_start_column):
    settings = cfml_format.get_setting(ds.scope_type, default={})
    multiline = settings.get("multiline", {})
    singleline_max_col = cfml_format.get_setting("singleline_max_col")
    after_comma_spacing = settings.get("after_comma_spacing")

    if not is_multiline(settings, singleline_max_col, ds, ds_start_column):
        return ds.inline_string

    el_indent_col = indent_column + cfml_format.tab_size
    indent = cfml_format.indent_to_column(indent_column)
    el_indent = cfml_format.indent_to_column(el_indent_col)
    start_col_offset = 0

    if multiline.get("leading_comma"):
        separator = "\n" + el_indent + ","
        start_col_offset += 1
        if after_comma_spacing and after_comma_spacing == "spaced":
            separator += " "
            start_col_offset += 1
    else:
        separator = ",\n" + el_indent
    formatted_str = "\n" + el_indent
    if multiline.get("leading_comma"):
        formatted_str += "  " if after_comma_spacing and after_comma_spacing == "spaced" else " "

    formatted_str += render_ds_element(cfml_format, ds.elements[0], el_indent_col, el_indent_col + start_col_offset)
    if len(ds.elements) > 1:
        formatted_str += separator
        formatted_str += separator.join([render_ds_element(cfml_format, e, el_indent_col, el_indent_col + start_col_offset) for e in ds.elements[1:]])

    formatted_str += "\n" + indent

    # break after first element
    if multiline.get("break_after_first_element", False):
        base_offset = ds_start_column - el_indent_col
        lines = formatted_str.split("\n")
        padding_inside = settings.get("padding_inside", None)

        indented_parts = []
        for line in lines[1:-1]:
            offset_line_indent = cfml_format.text_indent_columns(line) + base_offset
            if padding_inside is not None and padding_inside == "spaced":
                offset_line_indent += 1
            if multiline.get("leading_comma"):
                offset_line_indent -= 1
                if after_comma_spacing and after_comma_spacing == "spaced":
                    offset_line_indent -= 1
            indented_parts.append(cfml_format.indent_to_column(offset_line_indent) + line.lstrip())

        open_close_spacing = " " if padding_inside is not None and padding_inside == "spaced" else ""

        formatted_str = open_close_spacing + "\n".join(indented_parts).strip() + open_close_spacing

    return ds.inline_string[0] + formatted_str + ds.inline_string[-1]
