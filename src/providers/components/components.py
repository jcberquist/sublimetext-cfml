import math
from collections.abc import Callable
from typing import Any, NamedTuple

from ... import component_reference
from ...cfml_view import CfmlView, Documentation
from ...component_reference import ComponentReference
from . import (
    cfc_utils,
    cfcs,
    dot_path_completions,
    dot_path_documentation,
    entity_completions,
    entity_utils,
    variable_names,
)


class Finder(NamedTuple):
    """
    One kind of evidence for the project component that a position in a
    view refers to. Each function returns None when it finds nothing.
    """

    # the component, or the method of one, at the view's position
    find_reference: Callable[[CfmlView], ComponentReference | None]
    # the component of the method call whose arguments the position is in
    find_call_reference: Callable[[CfmlView], ComponentReference | None]
    # the methods of the component before the dot that was typed
    get_dot_completions: Callable[[CfmlView], list[Any] | None]
    get_inline_documentation: Callable[
        [CfmlView, ComponentReference], Documentation | None
    ] = component_reference.get_inline_documentation


def at_position(find_reference):
    def find(cfml_view):
        return find_reference(cfml_view, cfml_view.position)

    return find


def at_call(find_reference):
    # the call is looked up on what it is called on, when that is one name
    def find(cfml_view):
        dot_context = cfml_view.function_call_params.dot_context
        if len(dot_context) != 1:
            return None
        return find_reference(cfml_view, dot_context[0].name_region.begin())

    return find


# what is written in the source first, then the naming convention
FINDERS = [
    # `new foo.Bar()`, `createObject("component", "foo.Bar")`, `extends`, a
    # dot path string, or a variable assigned one of these
    Finder(
        at_position(cfc_utils.find_reference),
        at_call(cfc_utils.find_reference),
        dot_path_completions.get_dot_completions,
        dot_path_documentation.get_inline_documentation,
    ),
    # `entityNew("User")` and the entityLoad functions, or a variable
    # assigned one of these
    Finder(
        at_position(entity_utils.find_reference),
        at_call(entity_utils.find_reference),
        entity_completions.get_dot_completions,
    ),
    # a property with an inject attribute, by the bean or framework object
    # it asks for; otherwise a variable name, or a getter for one: the names
    # cfml_auto_variable_names gives every component of an automatic index,
    # or those the `variable_names` of `cfc_folders` give
    Finder(
        variable_names.find_cfc,
        variable_names.find_call_cfc,
        variable_names.get_dot_completions,
    ),
]


def span(reference, position):
    """The size of the smallest region of the reference around a position."""
    return min(
        (
            r.end() - r.begin()
            for r in reference.regions
            if r.begin() <= position <= r.end()
        ),
        default=math.inf,
    )


def find_references(cfml_view, find, position):
    """
    Returns the finders that find a reference, with the reference, the one
    closest around the position first. An argument of a call can be found
    both by itself and as part of the call, and is what the position is on;
    references that are as close are in the order of the finders.
    """
    found = []
    for finder in FINDERS:
        reference = find(finder)(cfml_view)
        if reference:
            found.append((finder, reference))
    return sorted(found, key=lambda pair: span(pair[1], position))


def first_answer(found, answer):
    for finder, reference in found:
        result = answer(finder, reference)
        if result is not None:
            return result
    return None


def references_at_position(cfml_view):
    # a view with no project can still name a component next to its file
    return find_references(
        cfml_view, lambda finder: finder.find_reference, cfml_view.position
    )


def lacks_method(cfml_view, reference):
    return reference.function_name is not None and not component_reference.has_method(
        cfml_view, reference
    )


def get_inline_documentation(cfml_view, doc_type):
    found = references_at_position(cfml_view)
    # a method that the component lacks gets the component's doc, where the
    # other capabilities have no answer and leave it to the next finder: so
    # that the doc is for what goto opens, a reference as close whose
    # component has the method comes first
    position = cfml_view.position
    found.sort(
        key=lambda pair: (span(pair[1], position), lacks_method(cfml_view, pair[1]))
    )
    return first_answer(
        found,
        lambda finder, reference: finder.get_inline_documentation(cfml_view, reference),
    )


def get_method_preview(cfml_view):
    return first_answer(
        references_at_position(cfml_view),
        lambda finder, reference: component_reference.get_method_preview(
            cfml_view, reference
        ),
    )


def get_goto_cfml_file(cfml_view):
    return first_answer(
        references_at_position(cfml_view),
        lambda finder, reference: component_reference.get_goto_cfml_file(
            cfml_view, reference
        ),
    )


def get_completion_docs(cfml_view):
    function_call_params = cfml_view.function_call_params
    # the dot context is set for a method call
    if not function_call_params or not function_call_params.dot_context:
        return None

    position = function_call_params.dot_context[0].name_region.begin()
    found = find_references(
        cfml_view, lambda finder: finder.find_call_reference, position
    )
    return first_answer(
        found,
        lambda finder, reference: component_reference.get_completion_doc(
            cfml_view, reference
        ),
    )


def get_dot_completions(cfml_view):
    for finder in FINDERS:
        completions = finder.get_dot_completions(cfml_view)
        if completions:
            return completions
    return None


def get_script_completions(cfml_view):
    # dot paths inside `createObject()` and after `new`, entity names inside
    # an entity function's first argument; one can be inside the other
    completions = [
        *(dot_path_completions.get_script_completions(cfml_view) or []),
        *(entity_completions.get_script_completions(cfml_view) or []),
    ]
    return completions or None


def build_project(project_name, project_data):
    cfcs.build_project_cfcs(project_name, project_data)
    dot_path_completions.build_project_map(project_name, project_data)
    entity_completions.build_project_entities(project_name, project_data)
