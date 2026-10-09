import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
JSON_PATH = ROOT / 'src/providers/language/json'


def load_generator():
    # scripts/ is not a package, so load the generator from its file
    path = ROOT / 'scripts' / 'build_completions.py'
    spec = importlib.util.spec_from_file_location('build_completions', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_completions = load_generator()


def param(name, required=True, type='string'):
    return {'name': name, 'type': type, 'required': required}


def fields_balanced(snippet):
    # every ${ opens a field that a later } closes; \ escapes the next char
    depth = 0
    i = 0
    while i < len(snippet):
        if snippet[i] == '\\':
            i += 2
            continue
        if snippet.startswith('${', i):
            depth += 1
            i += 2
            continue
        if snippet[i] == '}':
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


def test_required_only():
    params = [param('one'), param('two', type='numeric')]
    assert build_completions.build_params_completion(params) == (
        '${1:one}, ${2:two}',
        '${1:string one}, ${2:numeric two}',
    )


def test_optional_only():
    params = [param('one', False), param('two', False, 'boolean')]
    assert build_completions.build_params_completion(params) == (
        '',
        '${1:string one}${2:, ${3:boolean two}}',
    )


def test_required_then_optionals():
    params = [
        param('one'),
        param('two', False),
        param('three', False, 'boolean'),
    ]
    assert build_completions.build_params_completion(params) == (
        '${1:one}',
        '${1:string one}${2:, ${3:string two}}${4:, ${5:boolean three}}',
    )


def test_first_param_optional():
    # the first argument has no comma to fold into an optional field
    params = [param('one', False), param('two')]
    assert build_completions.build_params_completion(params) == (
        '${1:two}',
        '${1:string one}, ${2:string two}',
    )


def test_required_after_optional():
    params = [param('one'), param('two', False), param('three')]
    assert build_completions.build_params_completion(params) == (
        '${1:one}, ${2:three}',
        '${1:string one}${2:, ${3:string two}}, ${4:string three}',
    )


def member_completion(params, receiver=None):
    member = build_completions.member_params('fn', params, receiver)
    return build_completions.build_params_completion(member)


def test_member_receiver_first():
    params = [param('date', type='date'), param('mask', False)]
    assert member_completion(params) == ('', '${1:string mask}')


def test_member_receiver_not_first():
    # dateAdd(datepart, number, date) is date.add(datepart, number)
    params = [
        param('datepart'),
        param('number', type='numeric'),
        param('date', type='date'),
        param('timezone', False),
    ]
    assert member_completion(params, 'Date') == (
        '${1:datepart}, ${2:number}',
        '${1:string datepart}, ${2:numeric number}${3:, ${4:string timezone}}',
    )


def test_member_unknown_receiver():
    with pytest.raises(ValueError, match='no parameter'):
        member_completion([param('one'), param('two')], 'three')


def test_member_signature_required_only():
    params = [param('substring'), param('position', type='numeric')]
    assert (
        build_completions.member_signature('string', 'insert', params)
        == 'string.insert(substring, position)'
    )


def test_member_signature_required_then_optionals():
    params = [param('one'), param('two'), param('three', False), param('four', False)]
    assert (
        build_completions.member_signature('type', 'name', params)
        == 'type.name(one, two [, three] [, four])'
    )


def test_member_signature_first_param_optional():
    params = [param('first', False), param('second', False), param('third')]
    assert (
        build_completions.member_signature('type', 'name', params)
        == 'type.name([first] [, second], third)'
    )


def test_member_signature_no_params():
    assert build_completions.member_signature('type', 'name', []) == 'type.name()'


def write_members(tmp_path, monkeypatch, members):
    (tmp_path / 'completion_members.json').write_text(json.dumps(members))
    monkeypatch.setattr(build_completions, 'root', tmp_path)


def test_member_receiver_from_map(tmp_path, monkeypatch):
    members = {
        'date': {'DateFormat': 'format', 'DateAdd': {'name': 'add', 'receiver': 'date'}}
    }
    write_members(tmp_path, monkeypatch, members)
    assert build_completions.load_members() == {
        'dateformat': [['date', 'format', None]],
        'dateadd': [['date', 'add', 'date']],
    }


def test_member_of_two_types(tmp_path, monkeypatch):
    members = {
        'numeric': {'FormatBaseN': 'formatBaseN'},
        'string': {'FormatBaseN': 'formatBaseN'},
    }
    write_members(tmp_path, monkeypatch, members)
    assert build_completions.load_members() == {
        'formatbasen': [
            ['numeric', 'formatBaseN', None],
            ['string', 'formatBaseN', None],
        ]
    }


def test_member_listed_twice_in_a_type(tmp_path, monkeypatch):
    members = {'string': {'URLDecode': 'urlDecode', 'urlDecode': 'urlDecode'}}
    write_members(tmp_path, monkeypatch, members)
    with pytest.raises(ValueError, match='listed under string twice'):
        build_completions.load_members()


def test_members_with_one_name(tmp_path, monkeypatch):
    members = {'string': {'Trim': 'trim', 'RTrim': 'Trim'}}
    write_members(tmp_path, monkeypatch, members)
    with pytest.raises(ValueError, match='Trim and RTrim are both string.Trim'):
        build_completions.load_members()


def cfdocs_function(name, params):
    return {'type': 'function', 'name': name, 'syntax': f'{name}()', 'params': params}


def run_generator(tmp_path, monkeypatch, members, docs):
    # run main() over a cfdocs checkout of docs, returning what it writes
    write_members(tmp_path, monkeypatch, members)
    cfdocs = tmp_path / 'cfdocs'
    (cfdocs / 'data/en').mkdir(parents=True)
    for file_name, data in docs.items():
        (cfdocs / 'data/en' / file_name).write_text(json.dumps(data))
    out = tmp_path / 'out'
    out.mkdir()
    monkeypatch.setattr(build_completions, 'out_path', out)
    build_completions.main(cfdocs)
    return {p.name: p.read_text() for p in out.iterdir()}


def test_generator_emits_member_for_each_type(tmp_path, monkeypatch):
    members = {
        'numeric': {'FormatBaseN': 'formatBaseN'},
        'string': {'FormatBaseN': 'formatBaseN'},
    }
    docs = {
        'formatbasen.json': cfdocs_function(
            'formatBaseN', [param('number'), param('radix')]
        )
    }
    out = run_generator(tmp_path, monkeypatch, members, docs)
    member_functions = json.loads(out['cfml_member_functions.json'])
    assert sorted(member_functions) == ['numeric', 'string']
    # each with its own type as the receiver in the signature
    assert member_functions['numeric']['formatBaseN'][0] == 'numeric.formatBaseN(radix)'
    assert member_functions['string']['formatBaseN'][0] == 'string.formatBaseN(radix)'


def test_generator_member_signatures(tmp_path, monkeypatch):
    # cfdocs' own member signature is kept; one it lacks is built from the
    # parameters, without the receiver
    members = {
        'array': {'ArrayAppend': 'append'},
        'string': {'Find': {'name': 'find', 'receiver': 'string'}},
        'numeric': {'FormatBaseN': 'formatBaseN'},
    }
    append = cfdocs_function(
        'arrayAppend', [param('array'), param('value'), param('merge', False)]
    )
    append['member'] = 'someArray.append(value [, merge])'
    docs = {
        'arrayappend.json': append,
        'find.json': cfdocs_function(
            'find', [param('substring'), param('string'), param('start', False)]
        ),
        'formatbasen.json': cfdocs_function(
            'formatBaseN', [param('number'), param('radix')]
        ),
    }
    out = run_generator(tmp_path, monkeypatch, members, docs)
    member_functions = json.loads(out['cfml_member_functions.json'])
    signatures = {
        f'{t}.{name}': entry[0]
        for t, entries in member_functions.items()
        for name, entry in entries.items()
    }
    assert signatures == {
        'array.append': 'someArray.append(value [, merge])',
        'string.find': 'string.find(substring [, start])',
        'numeric.formatBaseN': 'numeric.formatBaseN(radix)',
    }


def test_generator_rejects_member_of_unknown_builtin(tmp_path, monkeypatch):
    members = {'list': {'ListLen': 'listLen', 'ToJSON': 'toJSON'}}
    docs = {'listlen.json': cfdocs_function('listLen', [param('list')])}
    with pytest.raises(ValueError, match='does not have: tojson$'):
        run_generator(tmp_path, monkeypatch, members, docs)


def generated_snippets():
    functions = json.loads((JSON_PATH / 'cfml_functions.json').read_text())
    for name, (_, snippets) in functions.items():
        for snippet in snippets:
            yield name, snippet
    members = json.loads((JSON_PATH / 'cfml_member_functions.json').read_text())
    for member_type, entries in members.items():
        for name, (_, snippets) in entries.items():
            for snippet in snippets:
                yield f'{member_type}.{name}', snippet


# members cfdocs documents under another name
MEMBER_ALIASES = {'serializejson': 'tojson'}


def test_member_names_are_builtin_names():
    # a member is named for its builtin, less any type prefix: arrayLen is
    # len and listLen is listLen
    members = json.loads((ROOT / 'scripts/completion_members.json').read_text())
    misnamed = []
    for member_type, builtins in members.items():
        for builtin, member in builtins.items():
            name = (member if isinstance(member, str) else member['name']).lower()
            builtin = builtin.lower()
            allowed = (
                builtin,
                builtin.removeprefix(member_type),
                MEMBER_ALIASES.get(builtin),
            )
            if name not in allowed:
                misnamed.append(f'{member_type}.{name}')
    assert misnamed == []


def test_generated_members_named_as_documented():
    # a member's signature names the method, as cfdocs documents it
    members = json.loads((JSON_PATH / 'cfml_member_functions.json').read_text())
    misnamed = []
    for member_type, entries in members.items():
        for name, (signature, _) in entries.items():
            method = re.match(r'\w+\.(\w+)', signature)
            if method is None or method[1].lower() != name.lower():
                misnamed.append(f'{member_type}.{name}')
    assert misnamed == []


def test_generated_member_signatures_list_required_params():
    # a member that takes a required argument says so in its signature;
    # only cfdocs' own signatures leave out its optional ones
    members = json.loads((JSON_PATH / 'cfml_member_functions.json').read_text())
    bare = []
    for member_type, entries in members.items():
        for name, (signature, (required, _)) in entries.items():
            if signature.endswith('()') and required != '()':
                bare.append(f'{member_type}.{name}')
    assert bare == []


def test_generated_snippet_fields_are_balanced():
    unbalanced = [name for name, s in generated_snippets() if not fields_balanced(s)]
    assert unbalanced == []


@pytest.mark.parametrize(
    'snippet, balanced',
    [
        ('${1:a}${2:, ${3:b}}', True),
        ('${1:a}${2:, ${3:b}', False),
        ('${1:a}}', False),
        ('${1:a\\}}', True),
    ],
)
def test_fields_balanced_checker(snippet, balanced):
    assert fields_balanced(snippet) is balanced


def test_generator_output_does_not_depend_on_file_order(tmp_path, monkeypatch):
    # two cfdocs files for one function, differing in their parameters
    docs = {
        'a.json': cfdocs_function('fooBar', [param('x', type='boolean')]),
        'b.json': cfdocs_function('FooBar', [param('y', type='boolean')]),
    }
    iterdir = Path.iterdir
    outputs = []
    for reverse in (False, True):
        monkeypatch.setattr(
            Path,
            'iterdir',
            lambda self, reverse=reverse: iter(sorted(iterdir(self), reverse=reverse)),
        )
        run_path = tmp_path / str(reverse)
        run_path.mkdir()
        outputs.append(run_generator(run_path, monkeypatch, {}, docs))
    assert outputs[0] == outputs[1]
