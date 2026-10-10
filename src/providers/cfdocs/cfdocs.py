import sublime
from ... import minihtml
from ... import utils
from ... import cfdocs_store
from ...cfml_view import CompletionDoc, Documentation, GotoCfmlFile

# the color of the side of the docs, a hue of the color scheme
ACCENT: minihtml.Hue = 'cyanish'
ERROR_ACCENT: minihtml.Hue = 'redish'

CFDOCS_ENGINES = {'coldfusion': 'ColdFusion', 'lucee': 'Lucee', 'openbd': 'OpenBD'}


def get_inline_documentation(cfml_view, doc_type):
    doc_name = None
    doc_attr_or_arg = None
    doc_regions = None
    doc_priority = 0

    if not utils.get_setting('cfdocs_enabled'):
        return None

    # tags
    if cfml_view.tag_name:
        doc_name = cfml_view.tag_name
        doc_attr_or_arg = cfml_view.tag_attribute_name

        if (
            doc_type == 'hover_doc'
            and doc_name in ['cfcomponent', 'cfinterface', 'cffunction']
            and cfml_view.view.match_selector(cfml_view.position, 'source.cfml.script')
        ):
            return None

    # functions
    elif cfml_view.view.match_selector(
        cfml_view.position, 'meta.function-call.support.cfml'
    ):
        doc_name, function_name_region, function_args_region = (
            cfml_view.get_function_call(cfml_view.position, True)
        )
        doc_regions = [
            sublime.Region(function_name_region.begin(), function_args_region.end())
        ]

    if doc_name:
        # while the doc is fetched, the other providers' docs show on their own
        result = cfdocs_store.get_cfdoc(doc_name, cfml_view.on_data_loaded)
        if result is None:
            return None
        data, success = result
        if success:
            return Documentation(
                doc_regions,
                build_cfdoc(doc_name, doc_attr_or_arg, data),
                None,
                doc_priority,
            )
        return Documentation(
            doc_regions, build_cfdoc_error(doc_name, data), None, doc_priority
        )

    return None


def get_completion_docs(cfml_view):
    if not utils.get_setting('cfdocs_enabled'):
        return None

    if (
        cfml_view.tag_name
        and cfml_view.tag_attribute_name
        and cfml_view.tag_location == 'tag_attributes'
    ):
        result = cfdocs_store.get_cfdoc(cfml_view.tag_name, cfml_view.on_data_loaded)
        if result is None:
            return None
        data, success = result
        if success:
            for param in data['params']:
                if param['name'].lower() == cfml_view.tag_attribute_name.lower():
                    return CompletionDoc(
                        None, build_tag_completion_doc(data, param), None, 0
                    )
        return None

    if (
        cfml_view.function_call_params
        and cfml_view.function_call_params.support
        and not cfml_view.function_call_params.method
    ):
        result = cfdocs_store.get_cfdoc(
            cfml_view.function_call_params.function_name, cfml_view.on_data_loaded
        )
        if result is None:
            return None
        data, success = result
        if success:
            return CompletionDoc(
                None,
                build_function_completion_doc(cfml_view.function_call_params, data),
                None,
                0,
            )

    return None


def get_goto_cfml_file(cfml_view):
    # functions
    if cfml_view.view.match_selector(
        cfml_view.position, 'meta.function-call.support.cfml'
    ):
        doc_name, function_name_region, function_args_region = (
            cfml_view.get_function_call(cfml_view.position, True)
        )

    # tags
    elif cfml_view.view.match_selector(
        cfml_view.position, 'meta.tag.cfml,meta.tag.script.cfml,meta.tag.script.cf.cfml'
    ):
        doc_name = utils.get_tag_name(cfml_view.view, cfml_view.position)
        if doc_name and doc_name[:2] != 'cf':
            # tag in script
            doc_name = 'cf' + doc_name

    else:
        return None

    if doc_name:
        return GotoCfmlFile('https://cfdocs.org/' + doc_name, None, 0)

    return None


def build_engine_badge(engine, minimum_version):
    text = CFDOCS_ENGINES[engine]
    if len(minimum_version) > 0:
        text += ' ' + minimum_version + '+'
    return minihtml.badge(text, 'engine')


def build_cfdoc(function_or_tag, attr_or_arg, data):
    cfdoc = minihtml.Doc(ACCENT, build_cfdoc_header(data, attr_or_arg))
    cfdoc.links = [
        {
            'href': 'https://cfdocs.org' + '/' + function_or_tag,
            'text': 'cfdocs.org' + '/' + function_or_tag,
        }
    ]

    cfdoc.body = minihtml.badges(
        build_engine_badge(engine, data['engines'][engine]['minimum_version'])
        for engine in sorted(CFDOCS_ENGINES)
        if engine in data['engines']
    )

    for param in data['params']:
        if attr_or_arg and param['name'].lower() == attr_or_arg.lower():
            header, body = build_attr_doc(param)
            cfdoc.body += minihtml.card(header, body)
            cfdoc.body += '\n'
            break
    else:
        cfdoc.body += minihtml.card(body=minihtml.clean_html(data['description']))

        if len(data['params']) > 0:
            cfdoc.body += minihtml.section(
                'Arguments' if data['type'] == 'function' else 'Attributes'
            )
            for param in data['params']:
                header, body = build_attr_doc(param)
                cfdoc.body += minihtml.card(header, body)
                cfdoc.body += '\n'

    cfdoc.body = minihtml.code_spans(cfdoc.body)

    return cfdoc


def format_values(values):
    return ', '.join(minihtml.clean_html(str(value)) for value in values)


def build_attr_doc(param):
    # cfdocs text is mostly plain, so tags it mentions (<cfoutput>) and
    # literal values (<b> as a default) are escaped; entities are kept
    header = minihtml.param_header(param)
    body = ''
    if 'default' in param and len(str(param['default'])):
        body += minihtml.paragraph(
            minihtml.labeled(
                'Default', minihtml.code(minihtml.clean_html(str(param['default'])))
            )
        )
    description = minihtml.clean_html(param['description']).strip()
    if len(description) > 0:
        body += minihtml.paragraph(description)
    if 'values' in param and len(param['values']):
        body += minihtml.paragraph(
            minihtml.labeled('Values', format_values(param['values']))
        )

    return header, body


def build_cfdoc_header(data, attr_or_arg=None, include_params=True):
    if data['type'] != 'function':
        header = '&lt;' + minihtml.span_wrap(data['name'], 'entity.name.tag.cfml')
        for param in data['params']:
            if attr_or_arg:
                if attr_or_arg.lower() != param['name'].lower():
                    continue
            elif not include_params or 'required' not in param or not param['required']:
                continue
            header += (
                ' '
                + minihtml.span_wrap(param['name'], 'entity.other.attribute-name')
                + '=""'
            )

        header += '&gt;'
        return header

    header = minihtml.span_wrap(data['name'], 'entity.name.function')
    header += '('

    param_base = ''
    if include_params:
        for param in data['params']:
            span_html = param_base + minihtml.span_wrap(
                param['name'], 'variable.parameter.function'
            )

            if 'required' not in param or not param['required']:
                span_html = '[' + span_html + ']'

            param_base = ', '
            header += span_html
    else:
        header += '...' if len(data['params']) > 0 else ''

    header += ')'

    if len(data['returns']) > 0:
        header += ': ' + minihtml.span_wrap(data['returns'], 'storage.type')

    return header


def build_cfdoc_error(function_or_tag, data):
    # the message is text, in paragraphs
    paragraphs = data['error_message'].split('\n\n')
    return minihtml.Doc(
        ERROR_ACCENT,
        'Uh oh!',
        'I tried to load that doc for you but got this instead:'
        + ''.join(minihtml.paragraph(minihtml.escape_text(p)) for p in paragraphs),
    )


def build_function_completion_doc(function_call_params, data):
    cfdoc = minihtml.Doc(ACCENT, build_cfdoc_header(data, include_params=False))

    arguments = []
    for index, param in enumerate(data['params']):
        if function_call_params.named_params:
            active_name = (
                function_call_params.params[function_call_params.current_index][0] or ''
            )
            is_active = active_name.lower() == param['name'].lower()
        else:
            is_active = index == function_call_params.current_index

        if is_active:
            description = minihtml.clean_html(param['description'])
            values = ''
            if 'values' in param and len(param['values']):
                values = minihtml.labeled('Values', format_values(param['values']))
            cfdoc.body = ''.join(
                minihtml.paragraph(markup) for markup in [description, values] if markup
            )
            arguments.append((param['name'], 'active'))
        elif param['required']:
            arguments.append((param['name'], 'required'))
        else:
            arguments.append((param['name'], 'optional'))

    if arguments:
        cfdoc.arguments = minihtml.argument_list(arguments)

    return cfdoc


def build_tag_completion_doc(data, param):
    cfdoc = minihtml.Doc(ACCENT)
    cfdoc.header = build_cfdoc_header(data, include_params=False)

    header, body = build_attr_doc(param)
    cfdoc.body = body
    cfdoc.arguments = minihtml.param_header(param)
    return cfdoc
