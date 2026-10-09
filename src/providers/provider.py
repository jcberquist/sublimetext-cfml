from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from ..cfml_view import (
    CfmlView,
    CompletionDoc,
    ContextType,
    Documentation,
    GotoCfmlFile,
    MethodPreview,
)

if TYPE_CHECKING:
    from ..component_index.index import ComponentProjectData


@dataclass(frozen=True, kw_only=True)
class Provider:
    """
    What a provider offers: completions by the context type of the view, and
    the functions that give its docs, goto files and method previews. Each
    returns None when it has nothing for the view.

    load is called once when the package loads, and the component index
    listener with each project's data as the index publishes it.
    """

    completions: Mapping[ContextType, Callable[[CfmlView], list[Any] | None]] = field(
        default_factory=dict
    )
    completion_docs: Callable[[CfmlView], CompletionDoc | None] | None = None
    goto_cfml_file: Callable[[CfmlView], GotoCfmlFile | None] | None = None
    inline_documentation: Callable[[CfmlView, str], Documentation | None] | None = None
    method_preview: Callable[[CfmlView], MethodPreview | None] | None = None
    load: Callable[[], None] | None = None
    component_index_listener: (
        Callable[[str, ComponentProjectData | None], None] | None
    ) = None

    def get_completion_docs(self, cfml_view):
        if self.completion_docs:
            return self.completion_docs(cfml_view)
        return None

    def get_completions(self, cfml_view):
        if cfml_view.type in self.completions:
            return self.completions[cfml_view.type](cfml_view)
        return None

    def get_goto_cfml_file(self, cfml_view):
        if self.goto_cfml_file:
            return self.goto_cfml_file(cfml_view)
        return None

    def get_inline_documentation(self, cfml_view, doc_type):
        if self.inline_documentation:
            return self.inline_documentation(cfml_view, doc_type)
        return None

    def get_method_preview(self, cfml_view):
        if self.method_preview:
            return self.method_preview(cfml_view)
        return None
