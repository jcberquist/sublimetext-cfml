import sublime
import sublime_plugin
import timeit
from functools import partial
from . import utils
from .component_parser import ComponentMetadata, ExtendedMetadata, parse_cfc_file_string
from .component_index import component_index


# how long a buffer must go unchanged before it is parsed again
PARSE_DELAY_MS = 500


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
        funct_regions = "meta.class.body.cfml comment.block.documentation.cfml, meta.function.declaration.cfml -meta.function.body.cfml"

        if not view.find_by_selector("meta.class.declaration.cfml"):
            # no component, as in a .cfs file or the script of a .cfm: every
            # doc comment is outside a class, and goes with the function
            # that it comes before
            script_selectors = []
            funct_regions = "comment.block.documentation.cfml -meta.function.body.cfml, meta.function.declaration.cfml -meta.function.body.cfml"

        for selector, separator in script_selectors:
            for r in view.find_by_selector(selector):
                min_string += view.substr(r) + separator

        for r in view.find_by_selector(funct_regions):
            string = view.substr(r)
            min_string += string + ("\n" if string.endswith("*/") else "{ }\n")

        min_string += "}"

    return min_string


def get_cached_view_metadata(view) -> ExtendedMetadata:
    """
    Returns the metadata of the component in a view, with what it inherits
    resolved against the component index of the view's project. Only the
    buffer's own declarations are cached, as the components it extends
    and the project's mappings can change while the buffer does not.
    """
    buffer_metadata = sublime_plugin.find_view_event_listener(
        view.buffer().primary_view(), BufferMetadata
    )
    if isinstance(buffer_metadata, BufferMetadata):
        base_meta = buffer_metadata.get()
    else:
        # not a CFML view, so nothing is kept for its buffer
        base_meta = parse_view_metadata(view)
    file_path = utils.normalize_path(view.file_name()) if view.file_name() else ""
    project_name = utils.get_project_name(view)
    return component_index.extend_metadata(project_name, file_path, base_meta)


def parse_view_metadata(view) -> ComponentMetadata:
    start_time = timeit.default_timer()
    file_string = get_minimal_file_string(view)
    base_meta = parse_cfc_file_string(file_string)

    if utils.get_setting("cfml_log_in_file_parse_time"):
        parse_time = timeit.default_timer() - start_time
        message = "CFML: parsed {} in {}ms"
        print(message.format(view.file_name() or "file", round(parse_time * 1000)))

    return base_meta


class BufferMetadata(sublime_plugin.ViewEventListener):
    """
    The metadata of the component in a CFML buffer, parsed again once the
    edits to the buffer pause. As a view event listener of the primary view
    only, there is one for each buffer, which the clones of the view share:
    Sublime Text creates it with the first CFML view of a buffer and drops
    it when the buffer closes or gets another syntax.
    """

    @classmethod
    def is_applicable(cls, settings):
        return utils.is_cfml_view(settings)

    def __init__(self, view):
        super().__init__(view)
        # the change count that was parsed, and the buffer's own metadata
        self.parsed: tuple[int, ComponentMetadata] | None = None
        # the change count that a parse is scheduled for
        self.scheduled: int | None = None

    def on_load_async(self):
        self.parse()

    def on_reload_async(self):
        self.parse()

    def on_revert_async(self):
        self.parse()

    def on_modified(self):
        # parse once the edits pause, so the last edit is always included
        self.scheduled = change_count = self.view.change_count()
        sublime.set_timeout_async(
            partial(self.parse_if_unchanged, change_count), PARSE_DELAY_MS
        )

    def parse_if_unchanged(self, change_count):
        if self.view.is_valid() and self.view.change_count() == change_count:
            self.parse()

    def parse(self):
        change_count = self.view.change_count()
        base_meta = parse_view_metadata(self.view)
        self.parsed = change_count, base_meta
        return base_meta

    def get(self) -> ComponentMetadata:
        """
        Returns the buffer's own metadata. While the parse for an edit is
        scheduled this is the metadata from before the edit; a change that
        no parse is scheduled for is parsed at once.
        """
        change_count = self.view.change_count()
        if self.parsed is None or change_count not in (self.parsed[0], self.scheduled):
            return self.parse()
        return self.parsed[1]
