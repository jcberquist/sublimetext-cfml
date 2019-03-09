import sublime
from ..cfml_plugins import basecompletions


def format_properties(cfml_format):
    sort_by = cfml_format.get_setting("format_properties.sort_by")

    if sort_by != "name":
        return []

    properties = cfml_format.find_by_selector(
        "source.cfml.script meta.tag.property.cfml"
    )
    property_names = cfml_format.find_by_selector(
        "source.cfml.script meta.tag.property.name.cfml"
    )

    if len(properties) != len(property_names):
        return

    sorted_properties = [
        r
        for r, name in sorted(
            zip(properties, property_names), key=lambda x: cfml_format.view.substr(x[1])
        )
    ]
    replacements = [
        (r, cfml_format.view.substr(sorted_r))
        for r, sorted_r in zip(properties, sorted_properties)
    ]

    return replacements


def normalize_builtin_functions(cfml_format):
    setting = cfml_format.get_setting("normalize_builtin_functions")
    substitutions = []

    if setting is None:
        return substitutions

    function_name_map = {
        funct.lower(): funct for funct in basecompletions.basecompletions.function_names
    }

    for r in cfml_format.find_by_selector("source.cfml.script support.function.cfml"):
        funct = cfml_format.view.substr(r).lower()
        substitutions.append((r, function_name_map[funct]))

    return substitutions


def normalize_strings(cfml_format):
    substitutions = []

    selectors = {
        "script": [
            {
                "base": "",
                "suffix": " -meta.tag.script.cfml -meta.class.declaration.cfml -meta.function.declaration.cfml",
            },
            {"base": "meta.function.parameters", "suffix": ""},
        ],
        "script-tag-attributes": [
            {"base": "meta.tag.script.cfml", "suffix": ""},
            {"base": "meta.class.declaration.cfml", "suffix": ""},
            {
                "base": "meta.function.declaration.cfml",
                "suffix": " -meta.function.parameters",
            },
        ],
    }

    def build_selector(key, selector):
        full_selector_list = []
        for d in selectors[key]:
            full_selector_list.append(
                "source.cfml.script " + d["base"] + " " + selector + d["suffix"]
            )
        return ",".join(full_selector_list)

    for key in selectors:
        key_setting = cfml_format.get_setting("normalize_strings." + key)

        if not key_setting or key_setting not in ["single", "double"]:
            continue

        quote = '"' if key_setting == "double" else "'"
        escaped_quote = '"' if key_setting == "single" else "'"
        opposite = "single" if key_setting == "double" else "double"

        start_selector = (
            "string.quoted."
            + opposite
            + ".cfml punctuation.definition.string.begin.cfml"
        )
        end_selector = (
            "string.quoted." + opposite + ".cfml punctuation.definition.string.end.cfml"
        )
        escaped_char_selector = (
            "string.quoted." + opposite + ".cfml constant.character.escape.quote.cfml"
        )
        meta_string_selector = (
            "meta.string.quoted."
            + opposite
            + ".cfml -punctuation.definition.string -constant.character.escape.quote.cfml"
        )

        for r in cfml_format.find_by_selector(build_selector(key, start_selector)):
            substitutions.append((r, quote))

        for r in cfml_format.find_by_selector(build_selector(key, end_selector)):
            substitutions.append((r, quote))

        for r in cfml_format.find_by_selector(
            build_selector(key, escaped_char_selector)
        ):
            substitutions.append((r, escaped_quote * int(r.size() / 2)))

        for r in cfml_format.find_by_selector(
            build_selector(key, meta_string_selector)
        ):
            for pt in range(r.begin(), r.end()):
                if cfml_format.view.substr(pt) == quote:
                    substitutions.append((sublime.Region(pt, pt + 1), (quote * 2)))

    return substitutions
