import sublime
from ruamel.yaml.comments import CommentedMap

ORDERED_KEYS = ['meta_scope', 'meta_content_scope', 'match', 'scope', 'captures', 'push', 'set', 'pop']

def order_output(syntax):
    def keysort(i):
        if len(i) == 1:
            return '0' + i
        return i

    if isinstance(syntax, dict):
        ordered_syntax = CommentedMap()
        for key in ORDERED_KEYS:
            if key in syntax:
                ordered_syntax[key] = order_output(syntax[key])
        for key in sorted(syntax, key=keysort):
            if key not in ORDERED_KEYS:
                ordered_syntax[key] = order_output(syntax[key])
        return ordered_syntax
    if isinstance(syntax, list):
        return [order_output(item) for item in syntax]
    return syntax

def attribute_value_string(char, scope, value_scope):
    syntax = {
        'match': char,
        'scope': 'punctuation.definition.string.begin.cfml',
        'set': [
            [
                {
                    'meta_scope': 'meta.string.quoted.{scope}.cfml string.quoted.{scope}.cfml'.format(scope = scope)
                },
                {
                    'match': char,
                    'scope': 'punctuation.definition.string.end.cfml',
                    'pop': True
                }
            ]
        ]
    }

    if '.' in value_scope and 'scope:' not in value_scope:
        # we have a scope name
        syntax['set'].append([
            {
                'meta_content_scope': value_scope
            },
            {
                'match': char * 2,
                'scope': 'constant.character.escape.quote.cfml',
            },
            {
                'match': r'(?=%s)' % char,
                'pop': True
            }
        ])
    else:
        # this is a context
        syntax['set'].append([
            {'include': value_scope},
            {'include': 'else-pop'}
        ])

    return syntax

def attribute_value_unquoted(value_scope):
    syntax = {
        'match': r'(?=[A-Za-z0-9\-_.$])',
        'set': [
            [
                { 'meta_scope': 'meta.string.unquoted.cfml string.unquoted.cfml' },
                { 'include': 'immediately-pop' }
            ]
        ]
    }

    if '.' in value_scope and 'scope:' not in value_scope:
        # we have a scope name
        syntax['set'].append([
            {
                'meta_scope': value_scope
            },
            {
                'match': r'(?=[^A-Za-z0-9\-_.$])',
                'pop': True
            }
        ])
    else:
        # this is a context
        syntax['set'].append([
            {'include': value_scope},
            {'include': 'else-pop'}
        ])

    return syntax


def load_tag_list():
    tags_to_filter = [
        'abort',
        'admin',
        'case',
        'catch',
        'component',
        'continue',
        'defaultcase',
        'else',
        'elseif',
        'exit',
        'finally',
        'function',
        'if',
        'interface',
        'rethrow',
        'retry',
        'return',
        'script',
        'servlet',
        'servletparam',
        'set',
        'sleep',
        'switch',
        'try',
        'while'
    ]
    tags = sublime.load_resource("Packages/CFML/src/basecompletions/json/cfml_tags.json")
    tags = sublime.decode_value(tags).keys()
    return [t.lower()[2:] for t in tags if t.lower()[2:] not in tags_to_filter]

def load_functions():

    functions = sublime.load_resource("Packages/CFML/src/basecompletions/json/cfml_functions.json")
    keys = [k.lower() for k in sublime.decode_value(functions)]

    prefixes = [
        'array',
        'struct',
        'component',
        'cache',
        'entity',
        'image',
        'date',
        'transaction',
        'xml',
        'spreadsheet',
        'orm',
        'object',
        'list',
        'query',
        'create',
        'get',
        'url',
        'is',
        'store',
        'to',
        'replace'
    ]

    prefixed = {}
    non_prefixed = []

    for item in sorted(keys):
        for prefix in prefixes:
            if item.startswith(prefix) and len(item) > len(prefix):
                prefixed.setdefault(prefix, []).append(item[len(prefix):])
                break
        else:
            non_prefixed.append(item)

    return prefixed, non_prefixed


def load_member_functions():

    member_functions = set()
    data = sublime.load_resource("Packages/CFML/src/basecompletions/json/cfml_member_functions.json")
    data = sublime.decode_value(data)

    for member_type in data:
        methods = [m.lower() for m in data[member_type].keys()]
        member_functions.update(methods)

    return list(member_functions)

