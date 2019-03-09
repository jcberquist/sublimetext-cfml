import timeit
from . import utils
from . import events
from .component_parser import parse_cfc_file_string
from .component_index import component_index


buffer_metadata_cache = {}


def get_minimal_file_string(view):
    min_string = ""

    tag_component_regions = view.find_by_selector("meta.class.cfml")

    if len(tag_component_regions) > 0:
        min_string += view.substr(tag_component_regions[0]) + "\n"
        current_funct = ""
        for r in view.find_by_selector(
            "meta.function.cfml, meta.function.body.tag.cfml meta.tag.argument.cfml"
        ):
            text = view.substr(r)
            if text.lower().startswith("<cff") and len(current_funct) > 0:
                min_string += current_funct + "</cffunction>\n"
                current_funct = ""
            current_funct += text + "\n"
        min_string += current_funct + "</cffunction>\n"
    else:
        script_selectors = [
            ("comment.block.documentation.cfml -meta.class", "\n"),
            ("meta.class.declaration.cfml", " {\n"),
            ("meta.tag.property.cfml", ";\n"),
        ]

        for selector, separator in script_selectors:
            for r in view.find_by_selector(selector):
                min_string += view.substr(r) + separator

        funct_regions = "meta.class.body.cfml comment.block.documentation.cfml, meta.function.declaration.cfml -meta.function.body.cfml"
        for r in view.find_by_selector(funct_regions):
            string = view.substr(r)
            min_string += string + ("\n" if string.endswith("*/") else "{ }\n")

        min_string += "}"

    return min_string


def get_cached_view_metadata(view):
    if view.buffer_id() in buffer_metadata_cache:
        return buffer_metadata_cache[view.buffer_id()][1]
    return get_view_metadata(view)


def get_view_metadata(view):
    start_time = timeit.default_timer()
    file_string = get_minimal_file_string(view)
    base_meta = parse_cfc_file_string(file_string)

    if utils.get_setting("cfml_log_in_file_parse_time"):
        parse_time = timeit.default_timer() - start_time
        message = "CFML: parsed {} in {}ms"
        print(message.format(view.file_name() or "file", round(parse_time * 1000)))

    extended_meta = dict(base_meta)
    extended_meta.update(
        {
            "functions": {},
            "function_file_map": {},
            "properties": {},
            "property_file_map": {},
        }
    )

    file_path = utils.normalize_path(view.file_name()) if view.file_name() else ""
    project_name = utils.get_project_name(view)
    if project_name and base_meta["extends"]:
        extends_file_path = component_index.resolve_path(
            project_name, file_path, base_meta["extends"]
        )
        root_meta = component_index.get_extended_metadata_by_file_path(
            project_name, extends_file_path
        )
        if root_meta:
            for key in [
                "functions",
                "function_file_map",
                "properties",
                "property_file_map",
            ]:
                extended_meta[key].update(root_meta[key])

    extended_meta["functions"].update(base_meta["functions"])
    extended_meta["function_file_map"].update(
        {funct_key: file_path for funct_key in base_meta["functions"]}
    )
    extended_meta["properties"].update(base_meta["properties"])
    extended_meta["property_file_map"].update(
        {prop_key: file_path for prop_key in base_meta["properties"]}
    )

    buffer_metadata_cache[view.buffer_id()] = timeit.default_timer(), extended_meta

    return extended_meta


def on_view_loaded(view):
    if not view.match_selector(0, "embedding.cfml"):
        return
    get_view_metadata(view)


def on_view_modified(view):
    if not view.match_selector(0, "embedding.cfml"):
        return

    if view.buffer_id() in buffer_metadata_cache:
        last_updated, meta = buffer_metadata_cache[view.buffer_id()]
        if timeit.default_timer() - last_updated < 0.5:
            return
    get_view_metadata(view)


def on_view_closed(view):
    if view.buffer_id() in buffer_metadata_cache:
        del buffer_metadata_cache[view.buffer_id()]


events.subscribe("on_load_async", on_view_loaded)
events.subscribe("on_modified_async", on_view_modified)
events.subscribe("on_close", on_view_closed)
