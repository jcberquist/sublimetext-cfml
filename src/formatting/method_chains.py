import sublime
from .. import utils


def format_method_chains(cfml_format):
    singleline_max_col = cfml_format.get_setting("singleline_max_col")
    break_after = cfml_format.get_setting("method_chains.break_after")
    inline = cfml_format.get_setting("method_chains.inline")

    substitutions = []
    method_chains = find_method_chains(cfml_format)

    for method_chain, method_chain_strs in reversed(method_chains):
        start_point = (
            utils.get_previous_character(cfml_format.view, method_chain[0].begin() - 1)
            + 1
        )
        target_region = sublime.Region(start_point, method_chain[-1].end())
        inline_str = ".".join(method_chain_strs)
        inline_method_cols = cfml_format.pt_column(
            start_point
        ) + cfml_format.text_columns(inline_str)

        # we need to break if total methods or total column size is greater than settings
        will_break = (
            (break_after is not None and break_after < len(method_chain_strs))
            or (
                singleline_max_col is not None
                and singleline_max_col < inline_method_cols
            )
            or ("\n" in inline_str)
        )

        formatted_str = ""
        for i, method_str in enumerate(method_chain_strs):
            # inline if method count and max column are within settings
            # if will_break then inline until start methods _or_ max column reached
            if not will_break or (inline is not None and inline > i):
                formatted_str += "." + method_str
            else:
                formatted_str += "\n" + "." + method_str
        substitutions.append((target_region, formatted_str))

    return substitutions


def find_method_chains(cfml_format):
    method_chains = []
    regions = cfml_format.find_by_selector(
        "source.cfml.script meta.function-call.method -meta.function-call.method.static"
    )

    if len(regions) == 0:
        return method_chains

    current_chain = [regions[0]]
    current_chain_strs = [cfml_format.view.substr(regions[0])]

    for r in regions[1:]:
        if (
            utils.get_next_character(cfml_format.view, current_chain[-1].end())
            == r.begin() - 1
        ):
            current_chain.append(r)
            current_chain_strs.append(cfml_format.view.substr(r))
        else:
            method_chains.append((current_chain, current_chain_strs))
            current_chain = [r]
            current_chain_strs = [cfml_format.view.substr(r)]

    method_chains.append((current_chain, current_chain_strs))
    return method_chains
