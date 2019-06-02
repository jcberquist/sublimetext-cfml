import sublime
from collections import namedtuple
from .. import utils

DELIMITED_SCOPES = {
    "struct": {
        "scope": "meta.struct-literal.cfml",
        "start": "punctuation.section.block.begin.cfml",
        "end": "punctuation.section.block.end.cfml",
        "separator": "punctuation.separator.struct-literal.cfml",
    },
    "array": {
        "scope": "meta.sequence.cfml",
        "start": "punctuation.section.brackets.begin.cfml",
        "end": "punctuation.section.brackets.end.cfml",
        "separator": "punctuation.separator.sequence.cfml",
    },
    "function_declaration": {
        "scope": "meta.function.parameters.cfml",
        "start": "punctuation.section.parameters.begin.cfml",
        "end": "punctuation.section.parameters.end.cfml",
        "separator": "punctuation.separator.parameter.function.cfml",
    },
    "function_call": {
        "scope": "meta.function-call.parameters",
        "start": "punctuation.section.group.begin.cfml",
        "end": "punctuation.section.group.end.cfml",
        "separator": "punctuation.separator.function-call",
    },
}

DELIMITED_SCOPE_LIST = [DELIMITED_SCOPES[k]["scope"] for k in DELIMITED_SCOPES]
DELIMITED_SCOPE_STARTS = [
    e["scope"] + " " + e["start"] for k, e in DELIMITED_SCOPES.items()
]


DelimitedScope = namedtuple(
    "DelimitedScope",
    "scope_type, scope_region, inline_string, has_multi_element_break, elements, element_regions",
)


def format_delimited_scopes(cfml_format):
    def scope_depth(scope_list):
        depth = 0
        for scope_name in scope_list:
            if any(scope_name.startswith(item) for item in DELIMITED_SCOPE_LIST):
                depth += 1
        return depth

    start_scope_list = (
        cfml_format.view.scope_name(cfml_format.region_to_format.begin() - 1)
        .rstrip()
        .split(" ")
    )
    depth = scope_depth(start_scope_list) + 1

    region_starts = []
    for r in cfml_format.find_by_selector(",".join(DELIMITED_SCOPE_STARTS)):
        for pt in range(r.begin(), r.end()):
            scope_name = cfml_format.view.scope_name(pt).rstrip()
            scope_list = scope_name.split(" ")
            if determine_scope_type(scope_list) and scope_depth(scope_list) == depth:
                region_starts.append(pt)
                break

    punctuation_pts = find_ds_punctuation(cfml_format)
    anon_functs = cfml_format.find_by_nested_selector("meta.function.anonymous.cfml")

    formatted_params = []

    for pt in region_starts:
        ds = parse_delimited_scope(cfml_format, pt, punctuation_pts)
        indent_column = cfml_format.line_indent_column(ds.scope_region.begin())
        ds_start_column = cfml_format.pt_column(ds.scope_region.begin())
        formatted_str = render_delimited_scope(
            cfml_format, ds, indent_column, ds_start_column, anon_functs
        )
        formatted_params.append((ds.scope_region, formatted_str))

    return formatted_params


def determine_scope_type(scope_list):
    for scope_type in DELIMITED_SCOPES:
        if (
            scope_list[-2].startswith(DELIMITED_SCOPES[scope_type]["scope"])
            and scope_list[-1] == DELIMITED_SCOPES[scope_type]["start"]
        ):
            return scope_type
    return None


def find_ds_punctuation(cfml_format):
    selectors = []
    for scope_type in DELIMITED_SCOPES:
        scope_dict = DELIMITED_SCOPES[scope_type]
        for key in ["start", "end", "separator"]:
            selectors.append(scope_dict["scope"] + " " + scope_dict[key])
    selector = ",".join(selectors)

    punctuation_regions = cfml_format.view.find_by_selector(selector)

    punctuation_pts = []
    for r in punctuation_regions:
        for pt in range(r.begin(), r.end()):
            punctuation_pts.append(pt)
    return punctuation_pts


def parse_delimited_scope(cfml_format, scope_pt, punctuation_pts):
    start_scope_list = cfml_format.view.scope_name(scope_pt).rstrip().split(" ")
    scope_type = determine_scope_type(start_scope_list)

    if not scope_type:
        print(
            "NO MATCH",
            scope_pt,
            cfml_format.view.substr(scope_pt),
            cfml_format.view.scope_name(scope_pt),
        )
        return

    base_scope = " ".join(start_scope_list[:-1])
    end_scope = base_scope + " " + DELIMITED_SCOPES[scope_type]["end"]
    delimiter_scope = base_scope + " " + DELIMITED_SCOPES[scope_type]["separator"]

    elements = []
    has_multi_element_break = False
    start_pt = scope_pt + 1
    current_element = []

    index = punctuation_pts.index(scope_pt)

    while True:
        index += 1
        current_pt = punctuation_pts[index]
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
            start_pt = current_pt + 1

        elif determine_scope_type(current_scope_parts):
            if start_pt != current_pt:
                current_element.append(sublime.Region(start_pt, current_pt))
            ds = parse_delimited_scope(cfml_format, current_pt, punctuation_pts)
            current_element.append(ds)
            if ds.has_multi_element_break:
                has_multi_element_break = True
            start_pt = ds.scope_region.end()
            index = punctuation_pts.index(start_pt - 1)

    element_count = cfml_format.get_setting(scope_type + ".multiline.element_count")
    if (
        element_count is not None
        and element_count >= 0
        and len(elements) >= element_count
    ):
        has_multi_element_break = True

    scope_region = sublime.Region(scope_pt, current_pt + 1)
    inline_string = render_delimited_scope_inline(
        cfml_format, scope_type, scope_region, elements
    )
    element_regions = get_element_regions(cfml_format, elements)
    return DelimitedScope(
        scope_type,
        scope_region,
        inline_string,
        has_multi_element_break,
        elements,
        element_regions,
    )


def get_element_regions(cfml_format, elements):
    element_regions = []
    for el in elements:
        if len(el) == 0:
            element_regions.append(None)
            continue

        start_pt = (
            el[0].scope_region.begin()
            if isinstance(el[0], DelimitedScope)
            else el[0].begin()
        )
        start_pt = utils.get_next_character(cfml_format.view, start_pt)

        end_pt = (
            el[-1].scope_region.end()
            if isinstance(el[-1], DelimitedScope)
            else el[-1].end()
        )
        end_pt = utils.get_previous_character(cfml_format.view, end_pt) + 1

        element_regions.append(sublime.Region(start_pt, end_pt))
    return element_regions


def render_delimited_scope_inline(cfml_format, scope_type, scope_region, elements):
    def render_element(el):
        el_str = ""
        for part in el:
            if isinstance(part, DelimitedScope):
                el_str += part.inline_string
            else:
                el_str += cfml_format.view.substr(part)
        return el_str.strip()

    after_comma_spacing = cfml_format.get_setting(scope_type + ".after_comma_spacing")
    separator = ", " if after_comma_spacing and after_comma_spacing == "spaced" else ","
    element_strs = [render_element(el) for el in elements]
    scope_string = separator.join(element_strs)

    padding_inside = cfml_format.get_setting(scope_type + ".padding_inside")
    if padding_inside is not None and padding_inside == "spaced":
        scope_string = " " + scope_string + " "

    if scope_string.strip() == "":
        empty_spacing = cfml_format.get_setting(scope_type + ".empty_spacing")
        if empty_spacing is not None and empty_spacing in ["compact", "spaced"]:
            scope_string = " " if empty_spacing == "spaced" else ""

    begin = cfml_format.view.substr(scope_region.begin())
    end = cfml_format.view.substr(scope_region.end() - 1)

    return begin + scope_string + end


def is_multiline(cfml_format, ds, ds_start_column):
    singleline_max_col = cfml_format.get_setting("singleline_max_col")
    multiline_min_length = cfml_format.get_setting(
        ds.scope_type + ".multiline.min_length"
    )
    region_columns = len(ds.inline_string)
    region_end_col = ds_start_column + region_columns

    if ds.has_multi_element_break and region_columns > multiline_min_length:
        return True

    if ds.inline_string.count("\n") > 0:
        return True

    if singleline_max_col > 0 and region_end_col > singleline_max_col:
        return True

    return False


def has_anon_funct_element(
    cfml_format, ds, ds_start_column, indent_column, anon_functs
):
    if ds.scope_type != "function_call":
        return False
    if len(ds.element_regions) < 1 or len(ds.element_regions) > 3:
        return False

    contained_functs = 0
    for e in ds.element_regions:
        if e in anon_functs:
            contained_functs += 1

    if contained_functs != 1:
        return False

    singleline_max_col = cfml_format.get_setting("singleline_max_col")
    lines = ds.inline_string.split("\n")
    if ds_start_column + len(lines[0]) > singleline_max_col:
        return False
    # for line in lines[1:]:
    #     if indent_column + len(line) > singleline_max_col:
    #         return False

    return True


def has_single_element(cfml_format, ds):
    if len(ds.elements) != 1:
        return False
    for e in ds.elements[0]:
        if isinstance(e, DelimitedScope):
            return e.scope_region == ds.element_regions[0]

    return True


def render_ds_element(cfml_format, el, indent_column, ds_start_column, anon_functs):
    el_str = ""
    for part in el:
        if isinstance(part, DelimitedScope):
            txt_lines = el_str.split("\n")
            if len(txt_lines) > 1:
                last_start_column = cfml_format.text_columns(txt_lines[-1]) + 1
                last_indent_column = cfml_format.text_indent_columns(txt_lines[-1])
            else:
                last_start_column = (
                    ds_start_column + cfml_format.text_columns(el_str) + 1
                )
                last_indent_column = indent_column

            el_str += render_delimited_scope(
                cfml_format, part, last_indent_column, last_start_column, anon_functs
            )
        else:
            el_str += cfml_format.view.substr(part)

    return el_str.strip()


def render_delimited_scope(
    cfml_format, ds, indent_column, ds_start_column, anon_functs
):
    if not is_multiline(cfml_format, ds, ds_start_column):
        return ds.inline_string

    el_indent_col = indent_column + cfml_format.tab_size
    rendered_elements = [
        render_ds_element(cfml_format, e, el_indent_col, el_indent_col, anon_functs)
        for e in ds.elements
    ]
    leading_comma = cfml_format.get_setting(ds.scope_type + ".multiline.leading_comma")
    after_comma_spacing = cfml_format.get_setting(
        ds.scope_type + ".after_comma_spacing"
    )

    anon_funct_element = has_anon_funct_element(
        cfml_format, ds, ds_start_column, indent_column, anon_functs
    )
    single_element = has_single_element(cfml_format, ds)

    separator = ",\n"
    pre = post = "\n"

    if leading_comma:
        separator = (
            "\n, " if after_comma_spacing and after_comma_spacing == "spaced" else "\n,"
        )

    if anon_funct_element or single_element:
        separator = (
            ", " if after_comma_spacing and after_comma_spacing == "spaced" else ","
        )
        padding_inside = cfml_format.get_setting(ds.scope_type + ".padding_inside")
        if padding_inside is not None and padding_inside == "spaced":
            pre = post = " "
        else:
            pre = post = ""

    formatted_str = pre + separator.join(rendered_elements) + post
    return ds.inline_string[0] + formatted_str + ds.inline_string[-1]
