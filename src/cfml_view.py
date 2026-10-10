import re
import sublime
from collections import defaultdict
from collections.abc import Callable
from enum import StrEnum
from functools import cached_property
from typing import NamedTuple
from . import minihtml
from . import utils
from . import buffer_metadata
from .component_parser import ExtendedMetadata


class ContextType(StrEnum):
    """Where the position of a CfmlView is, which decides what providers offer."""

    TAG = 'tag'
    TAG_ATTRIBUTES = 'tag_attributes'
    DOT = 'dot'
    SCRIPT = 'script'


# what the providers return, besides lists of completion items


class Documentation(NamedTuple):
    doc_regions: list[sublime.Region] | None
    content: minihtml.Doc
    on_navigate: Callable[[str], None] | None
    priority: int


class MethodPreview(NamedTuple):
    preview_regions: list[sublime.Region]
    content: minihtml.Preview
    on_navigate: Callable[[str], None] | None
    priority: int


class CompletionDoc(NamedTuple):
    doc_regions: list[sublime.Region] | None
    content: minihtml.Doc
    on_navigate: Callable[[str], None] | None
    priority: int


class GotoChoice(NamedTuple):
    """One of the files a goto could open, as a quick panel lists it."""

    # what the row shows: text, not markup
    label: str
    # shown under the label: markup, or "" for none
    details: str
    file_path: str
    symbol: str | None


class GotoCfmlFile(NamedTuple):
    file_path: str
    symbol: str | None
    priority: int
    # when the goto could be to more than one file, every one of them for
    # the user to choose from, the one above first; empty otherwise
    choices: tuple[GotoChoice, ...] = ()


class CfmlFunctionCallParams:
    param_regex = re.compile(r'^(?:([\w]+)\s*=\s*)?(.*)$', re.M | re.S)

    def __init__(self, cfml_view, position):
        self.support = False
        self.method = False
        self.dot_context = None
        self.named_params = False
        self.current_index = None
        self.params = []

        self.function_name, self.function_region, self.params_region = (
            cfml_view.get_function_call(position)
        )

        if (
            'support'
            in cfml_view.view.scope_name(self.function_region.begin())
            .strip()
            .split(' ')[-1]
        ):
            self.support = True

        prev_pt = self.function_region.begin() - 1
        if cfml_view.view.match_selector(
            prev_pt, 'source.cfml.script punctuation.accessor.cfml'
        ):
            self.method = True
            self.dot_context = cfml_view.dot_context = cfml_view.get_dot_context(
                prev_pt
            )

        start_scope_list = (
            cfml_view.view.scope_name(self.params_region.begin())
            .strip()
            .split(' ')[:-1]
        )
        separator_scope = (
            ' '.join(start_scope_list) + ' punctuation.separator.comma.cfml'
        )

        # walk the tokens rather than every point; a comma at this call's
        # level has exactly the call's scope plus the separator
        begin, end = self.params_region.begin() + 1, self.params_region.end()
        separators = [
            pt
            for r, scope in cfml_view.view.extract_tokens_with_scopes(
                sublime.Region(begin, end)
            )
            if scope.strip() == separator_scope
            for pt in range(r.begin(), r.end())
        ]

        if begin <= position < end:
            self.current_index = len([pt for pt in separators if pt < position])

        start = begin
        for pt in separators:
            current_element = cfml_view.view.substr(sublime.Region(start, pt)).strip()
            self.params.append(self.parse_param(current_element))
            start = pt + 1

        final_element = cfml_view.view.substr(sublime.Region(start, end - 1)).strip()
        if len(final_element) > 0 or start != begin:
            self.params.append(self.parse_param(final_element))

        if len(self.params) > 0:
            self.named_params = self.params[0][0] is not None

    @staticmethod
    def parse_param(element):
        """
        Returns (name, value) of an argument, with the name None when it is
        positional. The regex matches any string, so the fallback never runs.
        """
        match = CfmlFunctionCallParams.param_regex.match(element)
        return match.groups() if match else (None, element)

    def __repr__(self):
        return repr(
            (
                self.support,
                self.method,
                self.function_name,
                self.function_region,
                self.params_region,
                self.dot_context,
                self.named_params,
                self.current_index,
                self.params,
            )
        )


class CfmlView:
    def __init__(self, view, position, prefix=''):
        self.view = view
        self.prefix = prefix
        self.position = position
        self.function_call_params = None
        self.tag_name = None
        self.tag_attribute_name = None
        self.tag_in_script = False
        self.tag_location = None
        # called on the main thread when data that was still loading, such as
        # a cfdocs doc, becomes available; set by whoever displays the results
        self.on_data_loaded: Callable[[], None] | None = None

        self._cache = defaultdict(dict)

        self.prefix_start = self.position - len(self.prefix)
        self.determine_type()

        # continue processing only if we know the type
        if self.type:
            self.set_base_info()

    @cached_property
    def view_metadata(self) -> ExtendedMetadata:
        # the component in the view with what it inherits, resolved on first
        # use, as most lookups never ask for it
        return buffer_metadata.get_cached_view_metadata(self.view)

    def set_base_info(self):
        self.file_path = utils.normalize_path(self.view.file_name())
        self.file_name = (
            self.file_path.split('/').pop().lower() if self.file_path else None
        )
        self.project_name = utils.get_project_name(self.view)
        self.previous_char = self.view.substr(self.prefix_start - 1)

    def determine_type(self):
        # script is source.cfml.script, inside CFML files (embedding.cfml)
        # and as the whole of a .cfs file
        base_script_scope = 'source.cfml.script'
        script_tag_scope = (
            base_script_scope
            + ' meta.tag, '
            + base_script_scope
            + ' meta.class.declaration'
        )
        self.type: ContextType | None = None

        # dot completions (member and model function completions): decided
        # by the dot before the prefix, as what follows the caret may be the
        # end of the tag (`<cfset x = y.|>`)
        if self.view.match_selector(
            self.prefix_start - 1, base_script_scope + ' punctuation.accessor.cfml'
        ):
            self.type = ContextType.DOT
            self.set_dot_context()
            self.function_call_params = self.get_function_call_params(self.position)

        # tag completions
        elif self.view.match_selector(
            self.prefix_start, 'embedding.cfml - source.cfml.script'
        ):
            self.type = ContextType.TAG
            self.set_tag_info()

        # tag in script attribute completions: at the caret, or in the space
        # before it when what follows the caret ends the statement
        # (`http url="x" |;`, `component |{`)
        elif self.view.match_selector(
            self.prefix_start, script_tag_scope
        ) or self.view.match_selector(
            self.prefix_start - 1, '(' + script_tag_scope + ') - string'
        ):
            self.type = ContextType.TAG_ATTRIBUTES
            self.set_tag_info(True)

        # script completions
        elif self.view.match_selector(self.prefix_start, base_script_scope):
            self.type = ContextType.SCRIPT
            self.function_call_params = self.get_function_call_params(self.position)

    def set_dot_context(self):
        self.dot_context = self.get_dot_context(self.prefix_start - 1)

    def set_tag_info(self, tag_in_script=False):
        self.tag_in_script = tag_in_script

        tag_scope = (
            'meta.tag - punctuation.definition.tag.begin, meta.class.declaration.cfml'
        )
        # the point in the tag: the caret, or the space before it when what
        # follows the caret ends the tag's statement (`http url="x" |;`)
        tag_pt = self.prefix_start
        if (
            not self.view.match_selector(tag_pt, tag_scope)
            and tag_pt > 0
            and self.view.match_selector(tag_pt - 1, '(' + tag_scope + ') - string')
        ):
            tag_pt = tag_pt - 1

        if self.view.match_selector(tag_pt, tag_scope):
            if self.view.match_selector(
                self.prefix_start - 1,
                'punctuation.definition.tag.begin, entity.name.tag',
            ):
                self.tag_location = 'tag_name'
            elif self.view.match_selector(
                self.prefix_start, 'entity.other.attribute-name.cfml'
            ):
                self.tag_location = 'tag_attribute_name'
            else:
                self.tag_location = 'tag_attributes'

            if self.view.match_selector(
                tag_pt, 'source.cfml.script meta.class.declaration'
            ):
                self.tag_name = 'component'
            else:
                self.tag_name = utils.get_tag_name(self.view, tag_pt)

            if (
                self.tag_in_script
                and self.tag_name
                and not self.tag_name.startswith('cf')
            ):
                self.tag_name = 'cf' + self.tag_name

            if self.tag_location != 'tag_name':
                self.tag_attribute_name = utils.get_tag_attribute_name(
                    self.view, tag_pt
                )

                self.type = ContextType.TAG_ATTRIBUTES

    def get_dot_context(self, pt, cachable=True):
        if not cachable or pt not in self._cache['get_dot_context']:
            self._cache['get_dot_context'][pt] = utils.get_dot_context(self.view, pt)

        return self._cache['get_dot_context'][pt]

    def get_struct_context(self, pt, cachable=True):
        if not cachable or pt not in self._cache['get_struct_context']:
            self._cache['get_struct_context'][pt] = utils.get_struct_context(
                self.view, pt
            )

        return self._cache['get_struct_context'][pt]

    def get_struct_var_assignment(self, pt):
        struct_context = self.get_struct_context(pt)
        variable_name = '.'.join([symbol.name for symbol in reversed(struct_context)])
        return variable_name

    def get_function(self, pt, cachable=True):
        if not cachable or pt not in self._cache['get_function']:
            self._cache['get_function'][pt] = utils.get_function(self.view, pt)

        return self._cache['get_function'][pt]

    def get_function_call(self, pt, support=False, cachable=True):
        cache_key = (pt, support)

        if not cachable or cache_key not in self._cache['get_function_call']:
            self._cache['get_function_call'][cache_key] = utils.get_function_call(
                self.view, pt, support
            )

        return self._cache['get_function_call'][cache_key]

    def get_function_call_params(self, pt):
        if self.view.match_selector(
            pt, 'source.cfml.script meta.function-call.arguments'
        ):
            return CfmlFunctionCallParams(self, pt)
        return None

    def get_string_metadata(self, file_string):
        return buffer_metadata.parse_cfc_file_string(file_string)

    def find_variable_assignment(self, position, variable_name, cachable=True):
        cache_key = (position, variable_name)

        if not cachable or cache_key not in self._cache['find_variable_assignment']:
            var_assignment = utils.find_variable_assignment(
                self.view, position, variable_name
            )
            self._cache['find_variable_assignment'][cache_key] = var_assignment

        return self._cache['find_variable_assignment'][cache_key]
