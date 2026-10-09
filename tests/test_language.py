import json
import sys
import types
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).parent.parent
JSON_PATH = ROOT / 'src/providers/language/json'

MEMBER_FUNCTIONS = {
    'array': {
        'append': ['someArray.append(value [, merge])', ['(${1:value})', '()']],
        'each': ['array.each(callback)', ['(${1:callback})', '()']],
    },
    'query': {
        'append': ['qry.append(query2)', ['(${1:query2})', '()']],
        'each': ['array.each(callback)', ['(${1:callback})', '()']],
    },
    'string': {
        'each': [
            'string.each(callback, <delimiter> & more)',
            ['(${1:callback})', '()'],
        ],
    },
    'struct': {
        'append': ['destStruct.append(sourceStruct)', ['(${1:struct2})', '()']],
    },
    'date': {
        'add': ['date.add(datepart, number)', ['(${1:datepart})', '()']],
    },
}


def read_json(filename):
    return json.loads((JSON_PATH / (filename + '.json')).read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def language():
    # the cfdocs module loads certifi, which Sublime Text provides
    certifi = types.ModuleType('certifi')
    certifi.where = lambda: None
    with mock.patch.dict(sys.modules, {'certifi': certifi}):
        from CFML.src.providers.language import language

        yield language


def load_completions(language, monkeypatch, member_functions=None):
    def load_json_data(filename):
        if filename == 'cfml_member_functions' and member_functions is not None:
            return member_functions
        if filename in ('cfml_member_functions', 'cgi'):
            return read_json(filename)
        return {}

    monkeypatch.setattr(language, 'load_json_data', load_json_data)
    language.load_completions()


def dot_completions(language, monkeypatch, bif_completions='required'):
    monkeypatch.setattr(language.utils, 'get_setting', lambda key: bif_completions)
    cfml_view = types.SimpleNamespace(dot_context=[])
    return language.get_dot_completions(cfml_view)


def member_completions(language, monkeypatch):
    # CompletionItem is a stand-in that returns (args, kwargs)
    completions = {}
    for args, kwargs in dot_completions(language, monkeypatch):
        trigger, annotation, completion = args[:3]
        assert trigger not in completions
        completions[trigger] = (annotation, completion, kwargs['details'])
    return completions


def test_a_name_under_several_types_is_one_completion(language, monkeypatch):
    load_completions(language, monkeypatch, MEMBER_FUNCTIONS)
    completions = member_completions(language, monkeypatch)
    assert completions['append'] == (
        'array, query, struct',
        'append($0)',
        'someArray.append(value [, merge])'
        ' | qry.append(query2)'
        ' | destStruct.append(sourceStruct)',
    )


def test_identical_signatures_are_listed_once_and_escaped(language, monkeypatch):
    load_completions(language, monkeypatch, MEMBER_FUNCTIONS)
    completions = member_completions(language, monkeypatch)
    assert completions['each'] == (
        'array, query, string',
        'each($0)',
        'array.each(callback) | string.each(callback, &lt;delimiter&gt; &amp; more)',
    )


def test_a_single_type_name_is_a_bare_completion(language, monkeypatch):
    load_completions(language, monkeypatch, MEMBER_FUNCTIONS)
    completions = member_completions(language, monkeypatch)
    assert completions['add'] == ('date', 'add($0)', 'date.add(datepart, number)')


def test_member_completions_do_not_follow_the_bif_completions_setting(
    language, monkeypatch
):
    load_completions(language, monkeypatch, MEMBER_FUNCTIONS)
    basic = dot_completions(language, monkeypatch, 'basic')
    for setting in ('required', 'full'):
        assert dot_completions(language, monkeypatch, setting) == basic


def test_the_member_data_yields_one_completion_per_name(language, monkeypatch):
    load_completions(language, monkeypatch)
    names = [args[0].lower() for args, _ in dot_completions(language, monkeypatch)]
    assert len(names) == len(set(names))
    member_functions = read_json('cfml_member_functions')
    assert set(names) == {
        name.lower() for functs in member_functions.values() for name in functs
    }
