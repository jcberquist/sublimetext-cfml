import pytest

from CFML.src.component_parser import parse_cfc_file_string
from CFML.src.providers.components.inject import (
    Injection,
    find_class,
    load_classes,
    parse,
)


@pytest.mark.parametrize(
    'source',
    [
        'component {\n    property name="jwt" inject;\n    property name="mail" inject="";\n}',
        '<cfcomponent>\n<cfproperty name="jwt" inject>\n'
        '<cfproperty name="mail" inject="">\n</cfcomponent>',
    ],
)
def test_the_parser_stores_a_bare_inject_as_an_empty_value(source):
    properties = parse_cfc_file_string(source)['properties']
    assert properties['jwt']['meta']['inject'] == ''
    assert properties['mail']['meta']['inject'] == ''


@pytest.mark.parametrize(
    ('inject', 'bean_name'),
    [
        ('JWTService@cbsecurity', 'JWTService'),
        ('JWTService', 'JWTService'),
        ('id:JWTService@cbsecurity', 'JWTService'),
        ('ID:JWTService', 'JWTService'),
        ('model:JWTService', 'JWTService'),
        ('provider:JWTService@cbsecurity', 'JWTService'),
        ('provider:id:JWTService', 'JWTService'),
        (' JWTService ', 'JWTService'),
        # named after the property
        ('', 'jwt'),
        ('id', 'jwt'),
        ('model', 'jwt'),
        ('provider', 'jwt'),
        ('@cbsecurity', 'jwt'),
        ('id:@cbsecurity', 'jwt'),
    ],
)
def test_a_bean_is_named_by_the_attribute_or_the_property(inject, bean_name):
    assert parse(inject, 'jwt') == Injection(bean_name)


@pytest.mark.parametrize(
    'inject',
    [
        'coldbox',
        'WireBox',
        'executor',
        'entityService',
        'logbox:logger:{this}',
        'coldbox:setting:x',
        'java:java.util.UUID',
        'cbfs:disks:local',
    ],
)
def test_a_framework_dsl_is_not_a_bean(inject):
    assert parse(inject, 'jwt') == Injection(dsl=inject)


def test_a_provider_of_a_framework_object_is_its_dsl():
    assert parse('provider:coldbox:flash', 'flash') == Injection(dsl='coldbox:flash')


def test_what_a_method_of_a_bean_returns_is_neither():
    assert parse('model:jwtFactory:create', 'jwt') == Injection()


@pytest.mark.parametrize(
    ('dsl', 'class_path'),
    [
        ('coldbox', 'coldbox.system.web.Controller'),
        ('wirebox', 'coldbox.system.ioc.Injector'),
        ('CacheBox', 'coldbox.system.cache.CacheFactory'),
        (
            'coldbox:interceptorService',
            'coldbox.system.web.services.InterceptorService',
        ),
        (
            'coldbox:INTERCEPTORSERVICE',
            'coldbox.system.web.services.InterceptorService',
        ),
        ('logbox:root', 'coldbox.system.logging.Logger'),
        ('logbox:logger', 'coldbox.system.logging.Logger'),
        ('logbox:logger:{this}', 'coldbox.system.logging.Logger'),
        ('LogBox:Logger:contentbox', 'coldbox.system.logging.Logger'),
    ],
)
def test_the_table_gives_the_class_of_a_framework_dsl(dsl, class_path):
    assert find_class(dsl) == class_path


@pytest.mark.parametrize(
    'dsl',
    [
        'coldbox:setting:x',
        'coldbox:moduleSettings:x',
        'coldbox:configSettings',
        'coldbox:interceptorService:x',
        'logbox:loggers',
        'cachebox:default',
        'java:java.util.UUID',
        'entityService:Author',
    ],
)
def test_a_dsl_that_the_table_does_not_have_has_no_class(dsl):
    assert find_class(dsl) is None


def test_every_class_of_the_table_is_a_dot_path_of_coldbox():
    classes, prefixes = load_classes()
    assert prefixes == [('logbox:logger:', 'coldbox.system.logging.Logger')]
    for class_path in [*classes.values(), *(c for _, c in prefixes)]:
        assert class_path.startswith('coldbox.system.')
        assert all(part.isidentifier() for part in class_path.split('.'))
