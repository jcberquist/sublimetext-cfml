"""
Build the completion data in src/plugins_/basecompletions/json from a cfdocs
checkout (https://github.com/foundeo/cfdocs):

    python3 scripts/build_completions.py /path/to/cfdocs

Member function names come from completion_members.json. Run
scripts/build_base_cfscript_syntax.py afterwards to update the function and
tag names in the CFScript base syntax.
"""

import json
import pathlib
import re
import sys


root = pathlib.Path(__file__).resolve().parent
out_path = root.parent / 'src/plugins_/basecompletions/json'

# cfdocs spells these in lowercase
NAME_CASING = {
    'dbpoolclear': 'dbPoolClear',
    'isinthread': 'isInThread',
    'querylazy': 'queryLazy',
}


def load_members():
    src = json.loads((root / 'completion_members.json').read_text(encoding='utf-8'))
    out = {}
    for member_type, builtins in src.items():
        for builtin, member in builtins.items():
            out[builtin.lower()] = [member_type, member]
    return out


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
    if index > 1 and not param['required']:
        prefix = '${' + str(index) + ':'
        index += 1
    else:
        prefix = ''

    prefix += ', ${' if index > 1 else '${'
    wrapped = prefix + str(index) + ':' + param['type'] + ' ' + param['name'] + '}'
    return wrapped, index + 1


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

    for p in base_path.iterdir():
        data = json.loads(p.read_text(encoding='utf-8'))
        if is_boxlang_only(data):
            continue

        if data.get('type') == 'function':
            data = fix_casing(data)
            params_min, params_full = build_params_completion(data['params'])
            functions[data['name']] = [
                data['syntax'],
                ['(' + params_min + ')', '(' + params_full + ')'],
            ]

            function_param_completions = build_params(data['params'])
            if len(function_param_completions):
                function_params[data['name'].lower()] = function_param_completions

            if data['name'].lower() in members:
                member_type, member_name = members[data['name'].lower()]
                if member_type not in member_functions:
                    member_functions[member_type] = {}

                params_min, params_full = build_params_completion(data['params'][1:])
                member_functions[member_type][member_name] = [
                    data.get('member', f'{member_type}.{member_name}()'),
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

    write_json('cfml_functions.json', functions)
    write_json('cfml_function_params.json', function_params)
    write_json('cfml_member_functions.json', member_functions)
    write_json('cfml_tags.json', tags, False)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
