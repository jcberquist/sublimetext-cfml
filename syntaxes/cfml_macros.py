import re
from CFML.syntaxes import cfml_syntax

def meta(scope):
    syntax = [
        { 'meta_scope': scope },
        { 'include': 'immediately-pop' }
    ]
    return cfml_syntax.order_output(syntax)


def contexts(*contexts):
    return cfml_syntax.order_output([c for c in contexts])


def expect(name, scope):
    syntax = [
        { 'match': r'\b(?:%s)\b' % name, 'scope': scope, 'pop': True },
        {'include': 'else-pop'}
    ]
    return cfml_syntax.order_output(syntax)


def expect_context(context, exit_lookahead=None):
    syntax = [
        {'include': context}
    ]

    if exit_lookahead:
        syntax.insert(0, {
            'match': r'(?=%s)' % exit_lookahead,
            'pop': True
        })
    else:
        syntax.append({'include': 'else-pop'})

    return cfml_syntax.order_output(syntax)


def attribute(name, value_scope, name_scope=None, meta_scope=None):
    syntax = {
        'match': r'(?i:\b(?:%s)\b)' % name,
        'scope': 'entity.other.attribute-name.cfml' + (' ' + name_scope if name_scope else ''),
        'push': [
            {
                'match': '=',
                'scope': 'punctuation.separator.key-value.cfml',
                'set': [
                    cfml_syntax.attribute_value_string("'", "single", value_scope),
                    cfml_syntax.attribute_value_string('"', "double", value_scope),
                    cfml_syntax.attribute_value_unquoted(value_scope),
                    {
                        'include': 'else-pop'
                    }
                ]
            },
            {
                'include': 'else-pop'
            }
        ]
    }

    if meta_scope:
        syntax['push'] = [meta(meta_scope), syntax['push']]

    return cfml_syntax.order_output(syntax)


def function_call_params(meta_scope, named_param_scope, delimiter_scope):
    syntax = [
        {
            'match': r'\(',
            'scope': 'punctuation.section.group.begin.cfml',
            'set': [
                {
                    'meta_scope': meta_scope
                },
                {
                    'match': r'\)',
                    'scope': 'punctuation.section.group.end.cfml',
                    'pop': True
                },
                {
                    'match': ',',
                    'scope': delimiter_scope
                },
                {
                    'match': r'\b({{identifier}})\s*(=)(?!=)',
                    'captures': {
                        '1': named_param_scope,
                        '2': 'keyword.operator.assignment.cfml'
                    },
                    'push': 'expression-no-comma'
                },
                {
                    'match': r'(?=\S)',
                    'push': 'expression-no-comma'
                }
            ]
        },
        {
            'include': 'else-pop'
        }

    ]

    return cfml_syntax.order_output(syntax)


def block(push_or_set, meta_scope='meta.block.cfml'):
    syntax = {
        'match': r'\{',
        'scope': 'punctuation.section.block.begin.cfml',
        push_or_set: [
            {
                'meta_scope': meta_scope
            },
            {
                'match': r'\}',
                'scope': 'punctuation.section.block.end.cfml',
                'pop': True
            },
            {
                'include': 'statements'
            }
        ]
    }

    return cfml_syntax.order_output(syntax)


def keyword_control(name, scope, meta_scope, contexts='block'):
    syntax = {
        'match': r'\b(?:%s)\b' % name,
        'scope': 'keyword.control.%s.cfml' % scope,
        'push': [
            meta('meta.%s.cfml' % meta_scope),
            'block-scope'
        ]
    }

    if contexts == 'parens-block':
        syntax['push'].append('parens-scope')

    return cfml_syntax.order_output(syntax)


def template_expression(meta_content_scope, clear_scopes=None):
    push_context = [
        {
            'meta_content_scope': meta_content_scope
        },
        {
            'include': 'template-expression-contents'
        }
    ]

    if clear_scopes:
        push_context.insert(0, {'clear_scopes': clear_scopes})

    syntax = [
        {
            'match': '##',
            'scope': 'constant.character.escape.hash.cfml'
        },
        {
            'match': '#',
            'scope': 'punctuation.definition.template-expression.begin.cfml',
            'push': [
                {
                    'match': '#',
                    'scope': 'punctuation.definition.template-expression.begin.cfml',
                    'pop': True
                },
                {
                    'match': r'(?=.|\n)',
                    'push': push_context
                }
            ]
        }
    ]

    return cfml_syntax.order_output(syntax)


def tags(match):
    match_indent = len(re.search(r'^(.*)\{tags\}', match, flags=re.MULTILINE).group(1))
    tags = cfml_syntax.load_tag_list()
    tags_regex = '|'.join(sorted(tags))
    tags_regex =  re.sub(r'(.{80}[^|]*)', r'\1%s\n' % (' ' * match_indent), tags_regex)
    return match.replace('{tags}', tags_regex)


def functions(match):
    match_indent = len(re.search(r'^(.*)\{functions\}', match, flags=re.MULTILINE).group(1))
    prefixed, non_prefixed = cfml_syntax.load_functions()

    func_list = []

    for prefix in sorted(prefixed):
        string = prefix + "(?:" + "|".join(prefixed[prefix]) + ")"
        func_list.append(string)

    func_list.extend(non_prefixed)

    func_regex = '|'.join(func_list)
    func_regex =  re.sub(r'(.{80}[^|]*)', r'\1%s\n' % (' ' * match_indent), func_regex)
    return match.replace('{functions}', func_regex)


def member_functions(match):
    match_indent = len(re.search(r'^(.*)\{functions\}', match, flags=re.MULTILINE).group(1))
    functions = cfml_syntax.load_member_functions()
    func_regex = '|'.join(sorted(functions))
    func_regex =  re.sub(r'(.{80}[^|]*)', r'\1%s\n' % (' ' * match_indent), func_regex)
    return match.replace('{functions}', func_regex)
