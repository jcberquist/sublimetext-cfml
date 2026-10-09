# The shapes of the metadata the parser returns for a component file. A
# function, a parameter and a property also carry their other attributes
# and docblock tags, under the lower case name of each.

from typing import NotRequired, TypedDict


class Parameter(TypedDict):
    # the source text of the pattern for a destructuring parameter
    name: str
    required: bool
    type: str | None
    default: str | None
    hint: NotRequired[str]
    destructuring: NotRequired[bool]
    # a rest parameter, `...names`, which takes the arguments left
    rest: NotRequired[bool]


def parameter_label(parameter: Parameter) -> str:
    """Returns a parameter's name as a signature writes it: `...names` for a rest parameter."""
    return ('...' if parameter.get('rest') else '') + parameter['name']


class FunctionMeta(TypedDict):
    access: str
    returntype: str | None
    parameters: list[Parameter]
    hint: NotRequired[str]


class Function(TypedDict):
    name: str
    meta: FunctionMeta
    # an accessor generated for a property
    implicit: bool


class PropertyMeta(TypedDict):
    type: str
    # None when the property does not say
    getter: bool | None
    setter: bool | None
    inject: NotRequired[str]


class Property(TypedDict):
    name: str
    meta: PropertyMeta


class ComponentMetadata(TypedDict):
    accessors: bool
    persistent: bool
    extends: str | None
    initmethod: str | None
    entityname: str | None
    # both keyed by lower case name
    functions: dict[str, Function]
    properties: dict[str, Property]
    hint: NotRequired[str]


class ExtendedMetadata(ComponentMetadata):
    """
    The metadata of a component with the functions and properties of the
    components it extends merged in, as the component index resolves it. The
    file maps give the path of the file that declares each of them, which
    is an empty string in a buffer that has not been saved.
    """

    function_file_map: dict[str, str]
    property_file_map: dict[str, str]
