# The inject attribute of a property, by which WireBox, the dependency
# injection of ColdBox, sets the property: `property name="jwt"
# inject="JWTService@cbsecurity";`. Its value is a DSL, a namespace and its
# arguments separated by colons, or the name of a bean.

import functools
from typing import NamedTuple

from ... import utils

# the framework DSLs whose object is of a known class, and the dot path of
# the class; a row that ends in `:*` is that DSL with any arguments after
# it, as `logbox:logger:{this}`
DSLS_RESOURCE = 'src/providers/components/json/inject_dsls.json'

# the namespaces that name a bean: `id:UserService`, `model:UserService`
BEAN_NAMESPACES = frozenset(['id', 'model'])

# the namespaces of WireBox and of common modules that are a framework
# object, not a bean, when written alone: `inject="coldbox"` is the
# controller. Any other value with a colon is a DSL too, as a module can
# register its own namespace (`cbfs:disks:local`).
FRAMEWORK_NAMESPACES = frozenset(
    [
        'box',
        'bytype',
        'cachebox',
        'coldbox',
        'entityservice',
        'executor',
        'java',
        'logbox',
        'webservice',
        'wirebox',
    ]
)


class Injection(NamedTuple):
    """
    What an inject attribute asks for: a bean, a framework object, or
    neither when the object is the result of a method of a bean.
    """

    # the name of the bean, without the module it is from
    bean_name: str | None = None
    # the DSL of the framework object, without `provider:`
    dsl: str | None = None


def parse(inject: str, property_name: str) -> Injection:
    """
    Returns what an inject attribute asks for, read as WireBox reads it. A
    bare `inject` (an empty value) is the bean named after the property, as
    are `id`, `model` and `provider` alone. `provider:` asks for a provider
    of what follows it, which passes the calls on it to that object.
    """
    value = inject.strip()
    namespace, colon, rest = value.partition(':')
    namespace = namespace.lower()
    if namespace == 'provider':
        return parse(rest, property_name)
    if namespace in BEAN_NAMESPACES:
        if ':' in rest:
            # model:{name}:{method}: what a method of the bean returns
            return Injection()
        return Injection(bean_name(rest, property_name))
    if colon or namespace in FRAMEWORK_NAMESPACES:
        return Injection(dsl=value)
    return Injection(bean_name(value, property_name))


def bean_name(name: str, property_name: str) -> str:
    # `@cbsecurity` is the module the bean is from, which is not needed to
    # find it; `inject="@cbsecurity"` names the bean after the property
    return name.split('@', 1)[0].strip() or property_name


@functools.cache
def load_classes() -> tuple[dict[str, str], list[tuple[str, str]]]:
    """
    Returns the table of DSLs to classes, keyed in lower case, and the rows
    that take arguments after them, keyed by what the DSL starts with.
    """
    classes: dict[str, str] = {}
    prefixes: list[tuple[str, str]] = []
    for dsl, class_path in utils.load_json_resource(DSLS_RESOURCE).items():
        key = dsl.lower()
        if key.endswith(':*'):
            prefixes.append((key[:-1], class_path))
        else:
            classes[key] = class_path
    return classes, prefixes


def find_class(dsl: str) -> str | None:
    """
    Returns the dot path of the class of the object that a framework DSL
    asks for, or None when the table does not have the DSL. The DSL is
    matched without regard to case.
    """
    key = dsl.strip().lower()
    classes, prefixes = load_classes()
    if key in classes:
        return classes[key]
    for prefix, class_path in prefixes:
        if key.startswith(prefix):
            return class_path
    return None
