import re
import sublime
from collections import defaultdict
from collections import namedtuple
from . import utils
from . import buffer_metadata

CompletionList = namedtuple(
    "CompletionList", "completions priority exclude_lower_priority"
)
Documentation = namedtuple(
    "Documentation", "doc_regions doc_html_variables on_navigate priority"
)
MethodPreview = namedtuple(
    "MethodPreview", "preview_regions preview_html_variables on_navigate priority"
)
CompletionDoc = namedtuple(
    "CompletionDoc", "doc_regions doc_html_variables on_navigate"
)
GotoCfmlFile = namedtuple("GotoCfmlFile", "file_path symbol")


class CfmlFunctionCallParams:

    param_regex = re.compile(r"^(?:([\w]+)\s*=\s*)?(.*)$", re.M | re.S)

    def __init__(self, cfml_view, position):
        self.support = False
        self.method = False
        self.dot_context = None
        self.named_params = False
        self.current_index = None
        self.params = []

        self.function_name, self.function_region, self.params_region = cfml_view.get_function_call(
            position
        )

        if (
            "support"
            in cfml_view.view.scope_name(self.function_region.begin())
            .strip()
            .split(" ")[-1]
        ):
            self.support = True

        prev_pt = self.function_region.begin() - 1
        if cfml_view.view.match_selector(
            prev_pt, "embedding.cfml source.cfml.script punctuation.accessor.cfml"
        ):
            self.method = True
            self.dot_context = cfml_view.dot_context = cfml_view.get_dot_context(
                prev_pt
            )

        start_scope_list = (
            cfml_view.view.scope_name(self.params_region.begin())
            .strip()
            .split(" ")[:-1]
        )
        separator_scope = " ".join(start_scope_list) + " "
        last_key = start_scope_list[-2].replace("meta.", "punctuation.separator.") + " "
        for scope_name in ["entity.", "createcomponent.", "createjavaobject."]:
            last_key = last_key.replace(scope_name, "")
        separator_scope += last_key

        start = self.params_region.begin() + 1
        for pt in range(self.params_region.begin() + 1, self.params_region.end()):
            if pt == position:
                self.current_index = len(self.params)
            if cfml_view.view.scope_name(pt) == separator_scope:
                current_element = cfml_view.view.substr(
                    sublime.Region(start, pt)
                ).strip()
                param = re.match(CfmlFunctionCallParams.param_regex, current_element)
                self.params.append(param.groups())
                start = pt + 1

        final_element = cfml_view.view.substr(sublime.Region(start, pt)).strip()
        if len(final_element) > 0 or start != self.params_region.begin() + 1:
            param = re.match(CfmlFunctionCallParams.param_regex, final_element)
            self.params.append(param.groups())

        if len(self.params) > 0:
            self.named_params = self.params[0][0] is not None

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
    def __init__(self, view, position, prefix=""):
        self.view = view
        self.prefix = prefix
        self.position = position
        self.function_call_params = None
        self.tag_name = None
        self.tag_attribute_name = None
        self.tag_in_script = False
        self.tag_location = None

        self._cache = defaultdict(dict)
        self.CompletionList = CompletionList
        self.Documentation = Documentation
        self.CompletionDoc = CompletionDoc
        self.MethodPreview = MethodPreview
        self.GotoCfmlFile = GotoCfmlFile

        self.prefix_start = self.position - len(self.prefix)
        self.determine_type()

        # continue processing only if we know the type
        if self.type:
            self.set_base_info()
            self.view_metadata = buffer_metadata.get_cached_view_metadata(view)

    def set_base_info(self):
        self.file_path = utils.normalize_path(self.view.file_name())
        self.file_name = (
            self.file_path.split("/").pop().lower() if self.file_path else None
        )
        self.project_name = utils.get_project_name(self.view)
        self.previous_char = self.view.substr(self.prefix_start - 1)

    def determine_type(self):
        base_script_scope = "embedding.cfml source.cfml.script"
        self.type = None

        # tag completions
        if self.view.match_selector(
            self.prefix_start, "embedding.cfml - source.cfml.script"
        ):
            self.type = "tag"
            self.set_tag_info()

        # dot completions (member and model function completions)
        elif self.view.match_selector(
            self.prefix_start - 1, base_script_scope + " punctuation.accessor.cfml"
        ):
            self.type = "dot"
            self.set_dot_context()
            self.function_call_params = self.get_function_call_params(self.position)

        # tag in script attribute completions
        elif self.view.match_selector(
            self.prefix_start,
            base_script_scope
            + " meta.tag, "
            + base_script_scope
            + " meta.class.declaration",
        ):
            self.type = "tag_attributes"
            self.set_tag_info(True)

        # script completions
        elif self.view.match_selector(
            self.prefix_start, "embedding.cfml source.cfml.script"
        ):
            self.type = "script"
            self.function_call_params = self.get_function_call_params(self.position)

    def set_dot_context(self):
        self.dot_context = self.get_dot_context(self.prefix_start - 1)

    def set_tag_info(self, tag_in_script=False):
        self.tag_in_script = tag_in_script

        if self.view.match_selector(
            self.prefix_start,
            "meta.tag - punctuation.definition.tag.begin, meta.class.declaration.cfml",
        ):
            if self.view.match_selector(
                self.prefix_start - 1,
                "punctuation.definition.tag.begin, entity.name.tag",
            ):
                self.tag_location = "tag_name"
            elif self.view.match_selector(
                self.prefix_start, "entity.other.attribute-name.cfml"
            ):
                self.tag_location = "tag_attribute_name"
            else:
                self.tag_location = "tag_attributes"

            if self.view.match_selector(
                self.prefix_start, "source.cfml.script meta.class.declaration"
            ):
                self.tag_name = "component"
            else:
                self.tag_name = utils.get_tag_name(self.view, self.prefix_start)

            if self.tag_in_script and not self.tag_name.startswith("cf"):
                self.tag_name = "cf" + self.tag_name

            if self.tag_location != "tag_name":
                self.tag_attribute_name = utils.get_tag_attribute_name(
                    self.view, self.prefix_start
                )

                self.type = "tag_attributes"

    def get_dot_context(self, pt, cachable=True):
        if not cachable or pt not in self._cache["get_dot_context"]:
            self._cache["get_dot_context"][pt] = utils.get_dot_context(self.view, pt)

        return self._cache["get_dot_context"][pt]

    def get_struct_context(self, pt, cachable=True):
        if not cachable or pt not in self._cache["get_function"]:
            self._cache["get_struct_context"][pt] = utils.get_struct_context(
                self.view, pt
            )

        return self._cache["get_struct_context"][pt]

    def get_struct_var_assignment(self, pt):
        struct_context = self.get_struct_context(pt)
        variable_name = ".".join([symbol.name for symbol in reversed(struct_context)])
        return variable_name

    def get_function(self, pt, cachable=True):
        if not cachable or pt not in self._cache["get_function"]:
            self._cache["get_function"][pt] = utils.get_function(self.view, pt)

        return self._cache["get_function"][pt]

    def get_function_call(self, pt, support=False, cachable=True):
        cache_key = (pt, support)

        if not cachable or cache_key not in self._cache["get_function_call"]:
            self._cache["get_function_call"][cache_key] = utils.get_function_call(
                self.view, pt, support
            )

        return self._cache["get_function_call"][cache_key]

    def get_function_call_params(self, pt):
        if self.view.match_selector(
            pt, "source.cfml.script meta.function-call.parameters"
        ):
            return CfmlFunctionCallParams(self, pt)
        return None

    def get_string_metadata(self, file_string):
        return buffer_metadata.parse_cfc_file_string(file_string)

    def find_variable_assignment(self, position, variable_name, cachable=True):
        cache_key = (position, variable_name)

        if not cachable or cache_key not in self._cache["find_variable_assignment"]:
            var_assignment = utils.find_variable_assignment(
                self.view, position, variable_name
            )
            self._cache["find_variable_assignment"][cache_key] = var_assignment

        return self._cache["find_variable_assignment"][cache_key]
