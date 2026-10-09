import sys
import types
from pathlib import Path

import pytest

from CFML.src.component_index import component_index
from CFML.src.providers.provider import Provider

PROVIDERS = Path(__file__).parent.parent / 'src' / 'providers'


@pytest.fixture(scope='module')
def cfml_providers():
    from CFML.src import cfml_providers

    yield cfml_providers
    # the dispatcher tests import their own stand-in for the provider set,
    # which `from . import cfml_providers` skips while the package holds this
    del sys.modules['CFML.src.cfml_providers']
    delattr(sys.modules['CFML.src'], 'cfml_providers')


def provider_module(name, provider):
    module = types.ModuleType('CFML.src.providers.' + name)
    module.provider = provider
    return module


def test_every_provider_package_is_listed(cfml_providers):
    packages = {path.parent.name for path in PROVIDERS.glob('*/__init__.py')}
    listed = {module.__name__.rpartition('.')[2] for module in cfml_providers.modules}
    assert listed == packages
    assert cfml_providers.providers == [
        module.provider for module in cfml_providers.modules
    ]


def test_index_listeners_are_subscribed_once(cfml_providers, monkeypatch):
    listeners = [
        provider.component_index_listener
        for provider in cfml_providers.providers
        if provider.component_index_listener
    ]
    assert listeners
    for listener in listeners:
        assert component_index.listeners.count(listener) == 1

    # _plugin_loaded() runs again when cfml_plugin.py is reloaded
    subscribed = list(component_index.listeners)
    module = provider_module(
        'reloaded', Provider(component_index_listener=lambda name, data: None)
    )
    monkeypatch.setattr(cfml_providers, 'modules', [module])
    cfml_providers._plugin_loaded()
    cfml_providers._plugin_loaded()
    assert component_index.listeners == subscribed


def test_a_failing_load_does_not_stop_the_others(cfml_providers, monkeypatch, capsys):
    loaded = []

    def fail():
        loaded.append('failing')
        raise RuntimeError('no data')

    monkeypatch.setattr(
        cfml_providers,
        'modules',
        [
            provider_module('first', Provider(load=lambda: loaded.append('first'))),
            provider_module('failing', Provider(load=fail)),
            provider_module('no_load', Provider()),
            provider_module('last', Provider(load=lambda: loaded.append('last'))),
        ],
    )
    cfml_providers._plugin_loaded()

    assert loaded == ['first', 'failing', 'last']
    output = capsys.readouterr()
    assert 'CFML.src.providers.failing.provider.load() failed' in output.out
    assert 'RuntimeError: no data' in output.err


def test_provider_packages_leave_loading_to_cfml_providers(cfml_providers):
    # a hook left in a package would no longer be called
    for module in cfml_providers.modules:
        assert not hasattr(module, '_plugin_loaded'), module.__name__
