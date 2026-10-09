import sys
import types
from unittest import mock

import pytest

from CFML.src.cfml_view import CompletionDoc, GotoCfmlFile


def stand_in_modules():
    # stand-ins for the provider set, which would import every provider, and
    # for the view context
    cfml_providers = types.ModuleType('CFML.src.cfml_providers')
    cfml_providers.providers = []
    cfml_view = types.ModuleType('CFML.src.cfml_view')
    cfml_view.CfmlView = object

    return {
        'CFML.src.cfml_providers': cfml_providers,
        'CFML.src.cfml_view': cfml_view,
    }


@pytest.fixture(scope='module')
def dispatchers():
    with mock.patch.dict(sys.modules, stand_in_modules()):
        from CFML.src import completions, goto_cfml_file

        yield types.SimpleNamespace(
            completions=completions, goto_cfml_file=goto_cfml_file
        )


def provider(goto=None, completion_doc=None):
    return types.SimpleNamespace(
        get_goto_cfml_file=lambda cfml_view: goto,
        get_completion_docs=lambda cfml_view: completion_doc,
    )


def goto(name, priority):
    return GotoCfmlFile(name, None, priority)


def completion_doc(name, priority):
    return CompletionDoc(None, {'name': name}, None, priority)


def test_goto_takes_the_highest_priority_file(dispatchers, monkeypatch):
    providers = [
        provider(goto('cfdocs', 0)),
        provider(),
        provider(goto('component', 2)),
    ]
    monkeypatch.setattr(
        dispatchers.goto_cfml_file.cfml_providers, 'providers', providers
    )

    cfml_files = dispatchers.goto_cfml_file.get_cfml_files(None)
    assert [f.file_path for f in cfml_files] == ['component', 'cfdocs']


def test_goto_files_of_the_same_priority_keep_the_provider_order(
    dispatchers, monkeypatch
):
    providers = [provider(goto('first', 2)), provider(goto('second', 2))]
    monkeypatch.setattr(
        dispatchers.goto_cfml_file.cfml_providers, 'providers', providers
    )

    cfml_files = dispatchers.goto_cfml_file.get_cfml_files(None)
    assert [f.file_path for f in cfml_files] == ['first', 'second']


def test_completion_docs_are_ordered_by_priority(dispatchers, monkeypatch):
    providers = [
        provider(completion_doc=completion_doc('cfdocs', 0)),
        provider(),
        provider(completion_doc=completion_doc('first', 2)),
        provider(completion_doc=completion_doc('second', 2)),
    ]
    monkeypatch.setattr(dispatchers.completions.cfml_providers, 'providers', providers)

    docs = dispatchers.completions.get_completion_docs(None)
    assert [doc.content['name'] for doc in docs] == [
        'first',
        'second',
        'cfdocs',
    ]
