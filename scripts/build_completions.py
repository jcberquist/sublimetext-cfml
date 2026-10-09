"""
Build the completion data in src/providers/language/json from a cfdocs
checkout (https://github.com/foundeo/cfdocs):

    python3 scripts/build_completions.py /path/to/cfdocs

Member function names come from completion_members.json, along with the
parameter a member is called on where that is not the first one. Run
scripts/build_base_cfscript_syntax.py afterwards to update the function and
tag names in the CFScript base syntax.
"""

import json
import pathlib
import re
import sys


root = pathlib.Path(__file__).resolve().parent
out_path = root.parent / 'src/providers/language/json'

# cfdocs spells these in lowercase
NAME_CASING = {
    'dbpoolclear': 'dbPoolClear',
    'isinthread': 'isInThread',
    'querylazy': 'queryLazy',
}


def load_members():
    # builtin name -> a [type, name, receiver] for each member type the
    # builtin is a member function of
    src = json.loads((root / 'completion_members.json').read_text(encoding='utf-8'))
    out = {}
    for member_type, builtins in src.items():
        names = {}
        for builtin, member in builtins.items():
            # a member is its name, or {"name": ..., "receiver": ...} when
            # the value it is called on is not the first parameter
            if isinstance(member, str):
                member = {'name': member}
            mappings = out.setdefault(builtin.lower(), [])
            if any(m[0] == member_type for m in mappings):
                # JSON keys that differ only in case do not collide
                raise ValueError(f'{builtin} is listed under {member_type} twice')
            other = names.setdefault(member['name'].lower(), builtin)
            if other != builtin:
                raise ValueError(
                    f'{other} and {builtin} are both {member_type}.{member["name"]}'
                )
            mappings.append([member_type, member['name'], member.get('receiver')])
    return out


def member_params(name, params, receiver=None):
    # the parameters of the member function: the builtin's without the one
    # the member is called on, which is the first unless named
    if receiver is None:
        return params[1:]
    for i, p in enumerate(params):
        if p['name'].lower() == receiver.lower():
            return params[:i] + params[i + 1 :]
    raise ValueError(f'{name} has no parameter {receiver!r} to be the receiver')


def member_signature(member_type, member_name, params):
    # the signature in cfdocs' notation, for a member cfdocs has none for:
    # type.name(one, two [, three] [, four])
    out = ''
    for i, p in enumerate(params):
        comma = ', ' if i else ''
        if p['required']:
            out += comma + p['name']
        else:
            out += (' ' if i else '') + '[' + comma + p['name'] + ']'
    return f'{member_type}.{member_name}({out})'


def is_boxlang_only(data):
    engines = data.get('engines', {})
    return len(engines) > 0 and set(engines) == {'boxlang'}


def fix_casing(data):
    name = NAME_CASING.get(data['name'].lower())
    if name:
        data['name'] = name
        syntax = data['syntax']
        if syntax.lower().startswith(name.lower() + '('):
            data['syntax'] = name + syntax[len(name) :]
    return data


def wrap_param(param, index):
    prefix = ', ${' if index > 1 else '${'
    wrapped = prefix + str(index) + ':' + param['name'] + '}'
    return wrapped, index + 1


def wrap_param_full(param, index):
    field = param['type'] + ' ' + param['name']
    if index == 1:
        return '${1:' + field + '}', 2
    if param['required']:
        return ', ${' + str(index) + ':' + field + '}', index + 1
    # an optional parameter is its own field, comma included, so that
    # deleting the placeholder removes the whole argument
    inner = '${' + str(index + 1) + ':' + field + '}'
    return '${' + str(index) + ':, ' + inner + '}', index + 2


def build_params_completion(params):
    params_min, params_min_index = '', 1
    params_full, params_full_index = '', 1

    for p in params:
        if p['required']:
            param, params_min_index = wrap_param(p, params_min_index)
            params_min += param

        param, params_full_index = wrap_param_full(p, params_full_index)
        params_full += param

    return params_min, params_full


def is_description(value):
    # some cfdocs "values" are sentences describing the argument
    return (value.endswith('.') and not value.endswith('...')) or ': ' in value


def build_params(params):
    out = {}
    for p in params:
        values = [str(v) for v in p.get('values', [])]
        if p['type'] == 'boolean':
            # cfdocs types some callback arguments as boolean
            if p['name'].lower() != 'callback':
                out[p['name'].lower()] = ['true', 'false']
        elif len(values) and not any(is_description(v) for v in values):
            out[p['name'].lower()] = values
    return out


def sort_src(src, recurse):
    if not isinstance(src, dict):
        return src
    out = {}
    for k in sorted(src, key=lambda k: k.lower()):
        if recurse:
            out[k] = sort_src(src[k], recurse)
        else:
            out[k] = src[k]
    return out


def format_json(src, sort_nested=True):
    out = json.dumps(sort_src(src, sort_nested), indent=4)
    out = re.sub(r'\[\n\s*', r'[', out)
    out = re.sub(r',\n\s*\[', r', [', out)
    out = re.sub(r'",\n\s*"', r'", "', out)
    out = re.sub(r'"\n\s*\]', r'"]', out)
    out = re.sub(r'\]\n\s*\]', r']]', out)
    return out + '\n'


def write_json(file_name, src, sort_nested=True):
    (out_path / file_name).write_text(
        format_json(src, sort_nested), encoding='utf-8', newline='\n'
    )


def main(cfdocs_path):
    base_path = pathlib.Path(cfdocs_path) / 'data/en'
    members = load_members()

    functions = {}
    function_params = {}
    member_functions = {}
    tags = {}
    documented = set()

    # in a fixed order, so that the output does not depend on the file system
    for p in sorted(base_path.iterdir()):
        data = json.loads(p.read_text(encoding='utf-8'))
        if is_boxlang_only(data):
            continue

        if data.get('type') == 'function':
            data = fix_casing(data)
            documented.add(data['name'].lower())
            params_min, params_full = build_params_completion(data['params'])
            functions[data['name']] = [
                data['syntax'],
                ['(' + params_min + ')', '(' + params_full + ')'],
            ]

            function_param_completions = build_params(data['params'])
            if len(function_param_completions):
                function_params[data['name'].lower()] = function_param_completions

            for member_type, member_name, receiver in members.get(
                data['name'].lower(), []
            ):
                params = member_params(data['name'], data['params'], receiver)
                params_min, params_full = build_params_completion(params)
                if 'member' in data:
                    signature = data['member']
                else:
                    signature = member_signature(member_type, member_name, params)
                member_functions.setdefault(member_type, {})[member_name] = [
                    signature,
                    ['(' + params_min + ')', '(' + params_full + ')'],
                ]

        elif data.get('type') == 'tag' and not data['name'].lower().startswith('cf_'):
            # cf_ names are custom tags
            tag = {
                'attributes': [[], []],
                'attribute_values': build_params(data['params']),
            }

            for p in data['params']:
                idx = 0 if p['required'] else 1
                tag['attributes'][idx].append(p['name'])

            tag['attributes'][0].sort()
            tag['attributes'][1].sort()

            tags[data['name'].lower()] = tag

    undocumented = sorted(set(members) - documented)
    if undocumented:
        # a key with no cfdocs function would generate nothing
        raise ValueError(
            'completion_members.json lists builtins cfdocs does not have: '
            + ', '.join(undocumented)
        )

    write_json('cfml_functions.json', functions)
    write_json('cfml_function_params.json', function_params)
    write_json('cfml_member_functions.json', member_functions)
    write_json('cfml_tags.json', tags, False)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
