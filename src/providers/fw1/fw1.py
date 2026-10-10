import sublime
from ... import kinds
from ... import minihtml
from ... import utils
from ...cfml_view import Documentation


# the color of the side of the docs, a hue of the color scheme
ACCENT: minihtml.Hue = 'greenish'


fw1 = {'settings': {}, 'settings_docs': {}, 'methods': {}, 'methods_docs': {}}


def load():
    global fw1
    for key in fw1:
        data = load_json_data(key)
        if key == 'settings':
            data = {k: make_setting_completions(k, data[k]) for k in data}
        elif key == 'methods':
            data['calls'] = make_method_completions(data['calls'], 'framework.one')
            data['definitions'] = make_method_completions(
                data['definitions'], 'framework.one'
            )
            data['renderdata'] = make_method_completions(
                data['renderdata'], 'renderData()'
            )
        fw1[key] = data


def load_json_data(filename):
    return utils.load_json_resource('src/providers/fw1/json/' + filename + '.json')


def make_method_completions(source, details):
    completions = []
    for key in sorted(source.keys()):
        # keys are "name():returntype"
        name, returntype = key.split('():')
        completions.append(
            sublime.CompletionItem(
                name,
                returntype,
                name + source[key],
                sublime.CompletionFormat.SNIPPET,
                kind=kinds.METHOD,
                details=details,
            )
        )
    return completions


def make_setting_completions(prefix, source_list):
    return [
        sublime.CompletionItem(key, prefix, kind=kinds.SETTING)
        for key in sorted(source_list)
    ]


def extends_fw1(cfml_view):
    if cfml_view.view_metadata['extends']:
        return cfml_view.view_metadata['extends'] == 'framework.one'
    return False


def get_file_type(view):
    if not view.file_name():
        return ''
    file_path = view.file_name().replace('\\', '/').lower()
    for file_type in ['view', 'layout', 'controller']:
        for folder in utils.get_project_setting(
            view.window(), 'fw1_' + file_type + '_folders'
        ):
            if '/' + folder in file_path:
                return file_type
    return ''


def get_dot_completions(cfml_view):
    if (
        not utils.get_project_setting(cfml_view.view.window(), 'fw1_enabled')
        or len(cfml_view.dot_context) == 0
    ):
        return None

    if extends_fw1(cfml_view):
        if cfml_view.dot_context[-1].name == 'variables':
            key = '.'.join([symbol.name for symbol in reversed(cfml_view.dot_context)])
            if key in fw1['settings']:
                return fw1['settings'][key]
        if cfml_view.dot_context[-1].name in ['renderdata', 'renderer']:
            return fw1['methods']['renderdata']

    if get_file_type(cfml_view.view) == 'controller':
        if len(cfml_view.dot_context) > 1 and cfml_view.dot_context[-2].name in [
            'renderdata',
            'renderer',
        ]:
            return fw1['methods']['renderdata']
        if cfml_view.dot_context[-1].name in ['fw', 'framework']:
            return fw1['methods']['calls']

    return None


def get_script_completions(cfml_view):
    if not utils.get_project_setting(cfml_view.view.window(), 'fw1_enabled'):
        return None

    if extends_fw1(cfml_view):
        if cfml_view.view.match_selector(
            cfml_view.position,
            'meta.class.body.cfml -meta.function.body -meta.mapping',
        ):
            return fw1['methods']['definitions']

        key = cfml_view.get_struct_var_assignment(cfml_view.position)

        if key and key in fw1['settings']:
            return fw1['settings'][key]

        return fw1['methods']['calls']

    if get_file_type(cfml_view.view) in ['view', 'layout']:
        return fw1['methods']['calls']

    return None


def get_inline_documentation(cfml_view, doc_type):
    if not utils.get_project_setting(cfml_view.view.window(), 'fw1_enabled'):
        return None

    view_extends_fw1 = extends_fw1(cfml_view)
    view_file_type = get_file_type(cfml_view.view)

    # settings
    context = []
    word_region = cfml_view.view.word(cfml_view.position)

    if view_extends_fw1 and cfml_view.view.match_selector(
        cfml_view.position, 'variable.other.member'
    ):
        context = cfml_view.get_dot_context(word_region.begin() - 1)

    if view_extends_fw1 and cfml_view.view.match_selector(
        cfml_view.position, 'meta.class.body.cfml meta.mapping.cfml'
    ):
        context = cfml_view.get_struct_context(cfml_view.position)

    if len(context) > 0:
        key = '.'.join([symbol.name for symbol in reversed(context)])
        if cfml_view.view.match_selector(
            cfml_view.position, 'meta.mapping.key,variable.other'
        ):
            key += '.' + cfml_view.view.substr(word_region).lower()
        if key in fw1['settings_docs']:
            return Documentation(
                [word_region],
                get_documentation(key, fw1['settings_docs'][key]),
                None,
                2,
            )
        parent_key = '.'.join(key.split('.')[:-1])
        if parent_key in fw1['settings_docs']:
            return Documentation(
                [context[0].name_region, word_region],
                get_documentation(parent_key, fw1['settings_docs'][parent_key]),
                None,
                2,
            )

    # methods
    if view_extends_fw1 and cfml_view.view.match_selector(
        cfml_view.position, 'meta.function.declaration.cfml'
    ):
        function_name, function_name_region, function_region = cfml_view.get_function(
            cfml_view.position
        )
        region = sublime.Region(function_name_region.begin(), function_region.end())
        if function_name in fw1['methods_docs']:
            return Documentation(
                [region],
                get_documentation(function_name, fw1['methods_docs'][function_name]),
                None,
                2,
            )

    if view_extends_fw1 or view_file_type in ['view', 'layout']:
        if cfml_view.view.match_selector(cfml_view.position, 'meta.function-call'):
            function_name, function_name_region, function_args_region = (
                cfml_view.get_function_call(cfml_view.position)
            )
            region = sublime.Region(
                function_name_region.begin(), function_args_region.end()
            )
            if function_name in fw1['methods_docs']:
                return Documentation(
                    [region],
                    get_documentation(
                        function_name, fw1['methods_docs'][function_name]
                    ),
                    None,
                    2,
                )

    if view_file_type == 'controller' and cfml_view.view.match_selector(
        cfml_view.position, 'meta.function-call.method'
    ):
        function_name, function_name_region, function_args_region = (
            cfml_view.get_function_call(cfml_view.position)
        )
        region = sublime.Region(
            function_name_region.begin(), function_args_region.end()
        )
        if cfml_view.view.substr(function_name_region.begin() - 1) == '.':
            dot_context = utils.get_dot_context(
                cfml_view.view, function_name_region.begin() - 1
            )
            if (
                dot_context[-1].name in ['fw', 'framework']
                and function_name in fw1['methods_docs']
            ):
                return Documentation(
                    [region],
                    get_documentation(
                        function_name, fw1['methods_docs'][function_name]
                    ),
                    None,
                    2,
                )

    return None


def get_documentation(key, metadata):
    fw1_doc = minihtml.Doc(ACCENT)
    fw1_doc.header = metadata['header']
    fw1_doc.body = metadata['body']
    fw1_doc.links = metadata['links']
    return fw1_doc
