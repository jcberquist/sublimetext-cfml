import sublime
from typing import Any
from ... import kinds
from ... import minihtml
from ... import utils
from ...cfml_view import Documentation

# the color of the side of the docs, a hue of the color scheme
ACCENT: minihtml.Hue = 'cyanish'


appcfc: dict[str, Any] = {
    'settings': {},
    'settings_docs': {},
    'methods': {},
    'methods_docs': {},
}


def load():
    global appcfc
    for key in appcfc:
        data = load_json_data(key)
        if key == 'settings':
            data = {k: make_setting_completions(k, data[k]) for k in data}
        elif key == 'methods':
            data = [
                sublime.CompletionItem(
                    key,
                    'application.cfc',
                    key + data[key],
                    sublime.CompletionFormat.SNIPPET,
                    kind=kinds.METHOD,
                )
                for key in sorted(data.keys())
            ]
        appcfc[key] = data


def make_setting_completions(prefix, source_list):
    return [
        sublime.CompletionItem(key, prefix, kind=kinds.SETTING)
        for key in sorted(source_list)
    ]


def load_json_data(filename):
    return utils.load_json_resource(
        'src/providers/applicationcfc/json/' + filename + '.json'
    )


def get_dot_completions(cfml_view):
    if (
        cfml_view.file_name == 'application.cfc'
        and len(cfml_view.dot_context) > 0
        and cfml_view.dot_context[-1].name == 'this'
    ):
        key = '.'.join([symbol.name for symbol in reversed(cfml_view.dot_context)])
        if key in appcfc['settings']:
            return appcfc['settings'][key]

    return None


def get_script_completions(cfml_view):
    if cfml_view.file_name == 'application.cfc':
        if cfml_view.view.match_selector(
            cfml_view.position,
            'meta.class.body.cfml -meta.function -meta.mapping',
        ):
            return appcfc['methods']

        key = cfml_view.get_struct_var_assignment(cfml_view.position)
        if key and key in appcfc['settings']:
            return appcfc['settings'][key]

    return None


def get_inline_documentation(cfml_view, doc_type):
    if cfml_view.file_name != 'application.cfc':
        return None

    # settings
    context = []
    word_region = cfml_view.view.word(cfml_view.position)

    if cfml_view.view.match_selector(cfml_view.position, 'variable.other.member'):
        context = cfml_view.get_dot_context(word_region.begin() - 1)

    if cfml_view.view.match_selector(
        cfml_view.position, 'meta.class.body.cfml meta.mapping.cfml'
    ):
        context = cfml_view.get_struct_context(cfml_view.position)

    if len(context) > 0:
        key = '.'.join([symbol.name for symbol in reversed(context)])
        if cfml_view.view.match_selector(
            cfml_view.position,
            'variable.other.member, meta.mapping.key.cfml, variable.other.readwrite.cfml',
        ):
            key += '.' + cfml_view.view.substr(word_region).lower()
        if key in appcfc['settings_docs']:
            return Documentation(
                [word_region],
                get_documentation(key, appcfc['settings_docs'][key]),
                None,
                1,
            )
        parent_key = '.'.join(key.split('.')[:-1])
        if parent_key in appcfc['settings_docs']:
            return Documentation(
                [word_region, context[0].name_region],
                get_documentation(parent_key, appcfc['settings_docs'][parent_key]),
                None,
                1,
            )

    # methods
    if cfml_view.view.match_selector(
        cfml_view.position, 'meta.function.cfml, meta.function.declaration.cfml'
    ):
        function_name, function_name_region, function_region = cfml_view.get_function(
            cfml_view.position
        )
        region = sublime.Region(function_name_region.begin(), function_region.end())
        if function_name in appcfc['methods_docs']:
            return Documentation(
                [region],
                get_documentation(function_name, appcfc['methods_docs'][function_name]),
                None,
                1,
            )

    return None


def get_documentation(key, metadata):
    appcfc_doc = minihtml.Doc(ACCENT)
    appcfc_doc.header = metadata['header']
    appcfc_doc.body = metadata['body']
    appcfc_doc.links = [
        {
            'href': 'http://cfdocs.org/application-cfc',
            'text': 'cfdocs.org/application-cfc',
        }
    ]
    appcfc_doc.links.extend(metadata['links'])
    return appcfc_doc
