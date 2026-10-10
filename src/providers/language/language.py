from html import escape

import sublime
from ... import kinds
from ... import minihtml
from ... import utils
from ... import cfdocs_store
from ...cfml_view import Documentation


COMPLETION_FILES = [
    'cfml_tags',
    'cfml_functions',
    'cfml_member_functions',
    'cfml_function_params',
]


# the color of the side of the docs, a hue of the color scheme
ACCENT: minihtml.Hue = 'cyanish'


completions = {}
function_names = []
cgi = {}


def get_tags(cfml_view):
    return completions['cfml_tags']


def get_tag_attributes(cfml_view):
    if not cfml_view.tag_name:
        return None

    if (
        cfml_view.tag_attribute_name is None
        or cfml_view.tag_location == 'tag_attribute_name'
    ):
        # tag attribute completions
        completion_list = completions['cfml_tag_attributes'].get(
            cfml_view.tag_name, None
        )
        if completion_list:
            return completion_list
    elif (
        cfml_view.tag_name in completions['cfml_tag_attribute_values']
        and cfml_view.tag_attribute_name
        in completions['cfml_tag_attribute_values'][cfml_view.tag_name]
    ):
        # tag attribute value completions
        completion_list = completions['cfml_tag_attribute_values'][cfml_view.tag_name][
            cfml_view.tag_attribute_name
        ]
        return completion_list

    return None


def get_script_completions(cfml_view):
    completion_list = []

    if cfml_view.view.match_selector(
        cfml_view.position,
        'meta.function-call.arguments.cfml,meta.function-call.arguments.method.cfml',
    ):
        completion_list.append(
            sublime.CompletionItem(
                'argumentCollection',
                'parameter struct',
                'argumentCollection = ${1:parameters}',
                sublime.CompletionFormat.SNIPPET,
                kind=kinds.ARGUMENT,
            )
        )

    if cfml_view.view.match_selector(
        cfml_view.position, 'source.cfml.script meta.function-call.arguments'
    ):
        param_completions = get_param_completions(cfml_view)
        if param_completions:
            completion_list.extend(param_completions)
            return completion_list

    completion_list.extend(
        completions['cfml_functions'][utils.get_setting('cfml_bif_completions')]
    )
    completion_list.extend(completions['cfml_cf_tags_in_script'])
    completion_list.extend(completions['cfml_tags_in_script'])
    return completion_list


def get_dot_completions(cfml_view):

    if len(cfml_view.dot_context) == 1 and cfml_view.dot_context[0].name == 'cgi':
        return completions['cgi']

    return completions['cfml_member_functions']


def get_inline_documentation(cfml_view, doc_type):

    if cfml_view.view.match_selector(cfml_view.position, 'variable.other.member'):
        word = cfml_view.view.word(cfml_view.position)
        dot_context = cfml_view.get_dot_context(word.begin() - 1)
        if len(dot_context) == 1 and dot_context[0].name == 'cgi':
            key = 'cgi.' + cfml_view.view.substr(word).lower()
            if key in cgi:
                doc = minihtml.Doc(ACCENT, **cgi[key])
                return Documentation([word], doc, None, 1)

    return None


def load_completions():
    global completions, function_names, cgi
    completions_data = {
        filename: load_json_data(filename) for filename in COMPLETION_FILES
    }

    # tags
    completions['cfml_tags'] = []
    completions['cfml_tags_in_script'] = []
    completions['cfml_cf_tags_in_script'] = []
    completions['cfml_tag_attributes'] = {}
    completions['cfml_tag_attribute_values'] = {}
    for tag_name in sorted(completions_data['cfml_tags'].keys()):
        if isinstance(completions_data['cfml_tags'][tag_name], list):
            completions_data['cfml_tags'][tag_name] = {
                'attributes': completions_data['cfml_tags'][tag_name],
                'attribute_values': {},
            }
        tag_attributes = completions_data['cfml_tags'][tag_name]['attributes']
        completions['cfml_tags'].append(
            make_tag_completion(tag_name, tag_attributes[0])
        )
        completions['cfml_tags_in_script'].append(
            make_tag_completion(tag_name[2:], tag_attributes[0])
        )
        completions['cfml_cf_tags_in_script'].append(
            make_cf_script_tag_completion(tag_name, tag_attributes[0])
        )
        completions['cfml_tag_attributes'][tag_name] = [
            sublime.CompletionItem(
                a,
                'required',
                a + '="$1"',
                sublime.CompletionFormat.SNIPPET,
                kind=kinds.ATTRIBUTE,
            )
            for a in tag_attributes[0]
        ]
        completions['cfml_tag_attributes'][tag_name].extend(
            [
                sublime.CompletionItem(
                    a,
                    'optional',
                    a + '="$1"',
                    sublime.CompletionFormat.SNIPPET,
                    kind=kinds.ATTRIBUTE,
                )
                for a in tag_attributes[1]
            ]
        )
        # attribute values
        tag_attribute_values = completions_data['cfml_tags'][tag_name][
            'attribute_values'
        ]
        completions['cfml_tag_attribute_values'][tag_name] = {}
        for attribute_name in sorted(tag_attribute_values.keys()):
            completions['cfml_tag_attribute_values'][tag_name][attribute_name] = [
                sublime.CompletionItem(
                    v,
                    attribute_name,
                    v,
                    sublime.CompletionFormat.TEXT,
                    kind=kinds.VALUE,
                )
                for v in tag_attribute_values[attribute_name]
            ]

    # functions
    completions['cfml_functions'] = {'basic': [], 'required': [], 'full': []}
    function_names = []
    for funct in sorted(completions_data['cfml_functions'].keys()):
        completions['cfml_functions']['basic'].append(
            sublime.CompletionItem(
                funct,
                'cfml.fn',
                funct + '($0)',
                sublime.CompletionFormat.SNIPPET,
                kind=kinds.FUNCTION,
                details=completions_data['cfml_functions'][funct][0],
            )
        )
        completions['cfml_functions']['required'].append(
            sublime.CompletionItem(
                funct,
                'cfml.fn',
                funct + completions_data['cfml_functions'][funct][1][0],
                sublime.CompletionFormat.SNIPPET,
                kind=kinds.FUNCTION,
                details=completions_data['cfml_functions'][funct][0],
            )
        )
        completions['cfml_functions']['full'].append(
            sublime.CompletionItem(
                funct,
                'cfml.fn',
                funct + completions_data['cfml_functions'][funct][1][1],
                sublime.CompletionFormat.SNIPPET,
                kind=kinds.FUNCTION,
                details=completions_data['cfml_functions'][funct][0],
            )
        )

        function_names.append(funct)

    # function params
    completions['cfml_function_params'] = {}
    for funct in sorted(completions_data['cfml_function_params'].keys()):
        completions['cfml_function_params'][funct] = {}
        for param in sorted(completions_data['cfml_function_params'][funct].keys()):
            completions['cfml_function_params'][funct][param] = []
            for value in completions_data['cfml_function_params'][funct][param]:
                completions['cfml_function_params'][funct][param].append(
                    sublime.CompletionItem(
                        value,
                        param,
                        value,
                        kind=kinds.VALUE,
                    )
                )

    # member functions: the type of the value a member function is called on
    # is not known, so each name is offered once, with the types it belongs
    # to as the annotation and their signatures as the details
    member_functions = {}
    for member_function_type, functs in sorted(
        completions_data['cfml_member_functions'].items()
    ):
        for funct, funct_data in functs.items():
            member_functions.setdefault(funct.lower(), []).append(
                (funct, member_function_type, funct_data[0])
            )
    completions['cfml_member_functions'] = []
    for key in sorted(member_functions):
        names, member_types, signatures = zip(*member_functions[key], strict=True)
        completions['cfml_member_functions'].append(
            sublime.CompletionItem(
                names[0],
                ', '.join(member_types),
                names[0] + '($0)',
                sublime.CompletionFormat.SNIPPET,
                kind=kinds.METHOD,
                details=' | '.join(dict.fromkeys(map(escape, signatures))),
            )
        )

    # CGI scope
    cgi = load_json_data('cgi')
    completions['cgi'] = [
        sublime.CompletionItem(
            scope_variable.split('.').pop().upper(),
            'CGI Scope',
            kind=kinds.VARIABLE,
        )
        for scope_variable in sorted(cgi.keys())
    ]


def load_json_data(filename):
    return utils.load_json_resource('src/providers/language/json/' + filename + '.json')


def make_tag_completion(tag, required_attrs):
    attrs = ''
    for index, attr in enumerate(required_attrs, 1):
        attrs += ' ' + attr + '="$' + str(index) + '"'
    return sublime.CompletionItem(
        tag,
        'tag (cfml)',
        tag + attrs,
        sublime.CompletionFormat.SNIPPET,
        kind=kinds.TAG,
    )


def make_cf_script_tag_completion(tag, required_attrs):
    attrs = []
    for index, attr in enumerate(required_attrs, 1):
        attrs.append(' ' + attr + '="$' + str(index) + '"')
    return sublime.CompletionItem(
        tag,
        'tag (cfml)',
        tag + '(' + ','.join(attrs) + '$0 )',
        sublime.CompletionFormat.SNIPPET,
        kind=kinds.TAG,
    )


def get_param_completions(cfml_view):
    if (
        not cfml_view.function_call_params
        or not cfml_view.function_call_params.support
        or cfml_view.function_call_params.method
        or cfml_view.function_call_params.function_name
        not in completions['cfml_function_params']
    ):
        return None

    # the values are offered once the doc has been fetched
    result = cfdocs_store.get_cfdoc(cfml_view.function_call_params.function_name)
    if result is None:
        return None
    data, success = result
    if not success:
        return None

    active_param = get_active_param(data['params'], cfml_view.function_call_params)
    if not active_param:
        return None

    if (
        active_param
        not in completions['cfml_function_params'][
            cfml_view.function_call_params.function_name
        ]
    ):
        return None

    return completions['cfml_function_params'][
        cfml_view.function_call_params.function_name
    ][active_param]


def get_active_param(params, function_call_params):
    if len(params) > 0:
        for index, param in enumerate(params):
            if function_call_params.named_params:
                active_name = (
                    function_call_params.params[function_call_params.current_index][0]
                    or ''
                )
                is_active = active_name.lower() == param['name'].lower()
            else:
                is_active = index == function_call_params.current_index
            if is_active:
                return param['name'].lower()
    return None
