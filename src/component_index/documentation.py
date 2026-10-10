import sublime
from functools import partial
from .. import utils, minihtml
from ..component_parser.metadata import (
    ExtendedMetadata,
    Function,
    Property,
    parameter_label,
)


# the color of the side of the docs, a hue of the color scheme
ACCENT: minihtml.Hue = 'bluish'

# the href of the link to the other candidate at an index, after this
CANDIDATE_HREF = '__candidate_'
# how many other candidates the doc names, before "and N more"
SHOWN_CANDIDATES = 5


def get_documentation(
    view,
    extended_metadata: ExtendedMetadata,
    file_path,
    class_name,
    note='',
    *,
    folders,
):
    model_doc = build_documentation(
        extended_metadata, file_path, class_name, note, folders=folders
    )
    callback = partial(
        on_navigate, view, file_path, extended_metadata['function_file_map']
    )
    return model_doc, callback


def get_method_documentation(
    view,
    extended_metadata,
    file_path,
    function_name,
    class_name,
    method_name,
    method_preview,
    note='',
    *,
    folders,
):
    model_doc = build_method_documentation(
        extended_metadata,
        function_name,
        class_name,
        method_name,
        method_preview,
        note,
        folders=folders,
    )
    callback = partial(
        on_navigate, view, file_path, extended_metadata['function_file_map']
    )
    return model_doc, callback


def get_method_preview(
    view, extended_metadata, file_path, function_name, method_preview, *, folders
):
    model_doc = build_method_preview_doc(
        extended_metadata, function_name, method_preview, folders=folders
    )
    callback = partial(
        on_navigate, view, file_path, extended_metadata['function_file_map']
    )
    return model_doc, callback


def get_function_call_params_doc(
    extended_metadata, function_call_params, class_name, method_name
):
    model_doc = build_function_call_params_doc(
        extended_metadata, function_call_params, class_name, method_name
    )
    return model_doc, None


def color_scheme_key(view):
    # what the scratch panel below highlights with, as it gets the same
    # scheme settings as a CFML view: the scheme's name, as another scheme
    # can share the globals but color tokens differently, and its globals,
    # as with "auto" the scheme in use follows the OS light/dark mode
    settings = view.settings()
    color_scheme = settings.get('color_scheme')
    if color_scheme == 'auto':
        color_scheme = (
            settings.get('light_color_scheme'),
            settings.get('dark_color_scheme'),
        )
    return color_scheme, view.style()


def cached_method_preview(view, cache, function_file_path, function_name):
    current_scheme = color_scheme_key(view)
    if function_name not in cache or cache[function_name]['scheme'] != current_scheme:
        with open(function_file_path, encoding='utf-8') as f:
            file_string = f.read()
        # a scratch panel to highlight the file in; unlisted, so it never
        # shows up in the panel switcher
        cfml_minihtml_view = view.window().create_output_panel(
            'cfml_minihtml', unlisted=True
        )
        cfml_minihtml_view.assign_syntax(
            utils.package_resource_path('syntaxes/CFML.sublime-syntax')
        )
        cfml_minihtml_view.run_command(
            'append', {'characters': file_string, 'force': True, 'scroll_to_end': True}
        )
        cache[function_name] = {
            'scheme': current_scheme,
            'preview': build_method_preview(cfml_minihtml_view, function_name),
        }
        view.window().destroy_output_panel('cfml_minihtml')
    return cache[function_name]['preview']


def on_navigate(view, file_path, function_file_map, href):
    if href == '__go_to_component':
        view.window().open_file(file_path)
    else:
        file_path = function_file_map[href.lower()]
        view.window().run_command(
            'cfml_navigate_to_method', {'file_path': file_path, 'href': href}
        )


def build_candidates_note(guessed, labels):
    """
    Returns the line under the path of a doc that says the component was
    found by its name alone, and links to the other components it could
    be, by their labels: markup, or "" when there is neither to say.
    """
    if not guessed and not labels:
        return ''

    prose = 'matched by name' if guessed else ''
    links = ''
    if labels:
        prose += '; also:' if guessed else 'also:'
        shown = labels
        if len(labels) > SHOWN_CANDIDATES:
            shown = labels[: SHOWN_CANDIDATES - 1]
        links = ' ' + ', '.join(
            minihtml.link(CANDIDATE_HREF + str(index), minihtml.escape_text(label))
            for index, label in enumerate(shown)
        )
        if len(shown) < len(labels):
            links += ' and ' + str(len(labels) - len(shown)) + ' more'

    return minihtml.path_note(prose, links)


def candidate_index(href):
    """Returns the index of the candidate a link is to, if it is to one."""
    if href.startswith(CANDIDATE_HREF):
        return int(href[len(CANDIDATE_HREF) :])
    return None


def build_documentation(
    extended_metadata: ExtendedMetadata, file_path, class_name, note='', *, folders
):
    """
    Returns the doc of a component. Its path is shown as it is in the
    folders of the project, which may be none.
    """
    model_doc = minihtml.Doc(
        ACCENT, minihtml.span_wrap(class_name, 'entity.name.class')
    )

    if file_path:
        model_doc.body += minihtml.path('__go_to_component', file_path, folders)
    model_doc.body += note

    if 'hint' in extended_metadata and extended_metadata['hint']:
        model_doc.body += minihtml.card(
            body=minihtml.escape_text(extended_metadata['hint'])
        )

    if 'entityname' in extended_metadata and extended_metadata['entityname']:
        header = minihtml.header(
            'entityname', extended_metadata['entityname'], 'string.quoted'
        )
        model_doc.body += minihtml.card(header)

    if 'extends' in extended_metadata and extended_metadata['extends']:
        header = minihtml.header(
            'extends', extended_metadata['extends'], 'entity.other.inherited-class'
        )
        model_doc.body += minihtml.card(header)

    for key in ['accessors', 'persistent']:
        if extended_metadata[key]:
            header = minihtml.header(key, 'true', 'constant.language')
            model_doc.body += minihtml.card(header)

    if len(extended_metadata['properties']) > 0:
        properties = parse_properties(file_path, extended_metadata)
        if len(properties) > 0:
            model_doc.body += minihtml.section('Properties')
            for h, b in properties:
                model_doc.body += minihtml.card(h, b)

    if len(extended_metadata['functions']) > 0:
        functions = parse_functions(file_path, extended_metadata)
        if 'constructor' in functions:
            # we have a constructor
            model_doc.body += minihtml.section('Constructor')
            model_doc.body += minihtml.card(*functions['constructor'])

        if len(functions['public']) > 0:
            model_doc.body += minihtml.section('Public methods')
            for h, b in functions['public']:
                model_doc.body += minihtml.card(h, b)

        if len(functions['private']) > 0:
            model_doc.body += minihtml.section('Private methods')
            for h, b in functions['private']:
                model_doc.body += minihtml.card(h, b)

    return model_doc


def build_method_preview(cfml_minihtml_view, function_name):
    function_region = get_function_region(cfml_minihtml_view, function_name)
    return minihtml.from_view(cfml_minihtml_view, function_region)


def build_method_header(funct: Function, class_name, method_name):
    """Returns the header of a method's docs: its signature without arguments."""
    header = ''
    if class_name:
        header += minihtml.span_wrap(class_name, 'entity.name.class')
        if method_name:
            header += '.'
    if method_name:
        header += minihtml.span_wrap(method_name, 'entity.name.function') + '()'
    if funct['meta']['access'] and len(funct['meta']['access']) > 0:
        header = (
            minihtml.span_wrap(funct['meta']['access'], 'storage.modifier')
            + ' '
            + header
        )
    if funct['meta']['returntype'] and len(funct['meta']['returntype']) > 0:
        header += ': ' + minihtml.span_wrap(funct['meta']['returntype'], 'storage.type')
    return header


def build_method_documentation(
    extended_metadata: ExtendedMetadata,
    function_name,
    class_name,
    method_name,
    method_preview=None,
    note='',
    *,
    folders,
):
    function_file_path = extended_metadata['function_file_map'][function_name]

    funct = extended_metadata['functions'][function_name]
    model_doc = minihtml.Doc(
        ACCENT, build_method_header(funct, class_name, method_name)
    )
    model_doc.body = minihtml.path(funct['name'], function_file_path, folders) + note

    if 'hint' in funct['meta'] and funct['meta']['hint']:
        model_doc.body += minihtml.card(
            body=minihtml.escape_text(funct['meta']['hint'])
        )

    if len(funct['meta']['parameters']) > 0:
        model_doc.body += minihtml.section('Arguments')
        for arg in funct['meta']['parameters']:
            header = minihtml.param_header(arg)
            body = ''
            if arg['default']:
                body += minihtml.paragraph(
                    minihtml.labeled(
                        'Default',
                        minihtml.code(minihtml.escape_text(str(arg['default']))),
                    )
                )
            if 'hint' in arg and arg['hint']:
                body += minihtml.escape_text(arg['hint'])
            model_doc.body += minihtml.card(header, body)
            model_doc.body += '\n'

    if method_preview:
        model_doc.body += method_preview

    return model_doc


def build_method_preview_doc(
    extended_metadata: ExtendedMetadata, function_name, method_preview, *, folders
):
    function_file_path = extended_metadata['function_file_map'][function_name]
    funct = extended_metadata['functions'][function_name]
    return minihtml.Preview(
        minihtml.path_link(funct['name'], function_file_path, folders, plain=True),
        method_preview,
    )


def build_function_call_params_doc(
    extended_metadata: ExtendedMetadata, function_call_params, class_name, method_name
):
    funct = extended_metadata['functions'][function_call_params.function_name]
    model_doc = minihtml.Doc(
        ACCENT, build_method_header(funct, class_name, method_name)
    )

    arguments = []
    for index, arg in enumerate(funct['meta']['parameters']):
        if function_call_params.named_params:
            active_name = (
                function_call_params.params[function_call_params.current_index][0] or ''
            )
            is_active = active_name.lower() == arg['name'].lower()
        else:
            is_active = index == function_call_params.current_index

        if is_active:
            default = ''
            if arg['default']:
                default = minihtml.labeled(
                    'Default', minihtml.code(minihtml.escape_text(arg['default']))
                )
            model_doc.body += minihtml.lines(
                [
                    minihtml.labeled(
                        'Type',
                        minihtml.signature(
                            minihtml.span_wrap(arg['type'] or 'any', 'storage.type')
                        ),
                    ),
                    minihtml.labeled(
                        'Required', 'true' if arg['required'] else 'false'
                    ),
                    default,
                ]
            )
            if 'hint' in arg and arg['hint']:
                model_doc.body += minihtml.paragraph(minihtml.escape_text(arg['hint']))

            arguments.append((parameter_label(arg), 'active'))
        elif arg['required']:
            arguments.append((parameter_label(arg), 'required'))
        else:
            arguments.append((parameter_label(arg), 'optional'))

    if arguments:
        model_doc.arguments = minihtml.argument_list(arguments)

    return model_doc


def parse_functions(file_path, metadata: ExtendedMetadata):
    result = {}
    constructor = metadata['initmethod'].lower() if metadata['initmethod'] else 'init'
    functions = metadata['functions']
    function_file_map = metadata['function_file_map']
    public_functions = [
        (functions[key], function_file_map[key])
        for key in sorted(functions)
        if key != constructor and is_public_function(functions[key])
    ]
    private_functions = [
        (functions[key], function_file_map[key])
        for key in sorted(functions)
        if key != constructor and not is_public_function(functions[key])
    ]
    result['public'] = [
        parse_function(function, funct_file_path, file_path)
        for function, funct_file_path in public_functions
    ]
    result['private'] = [
        parse_function(function, funct_file_path, file_path)
        for function, funct_file_path in private_functions
    ]
    if constructor in functions:
        result['constructor'] = parse_function(
            functions[constructor], function_file_map[constructor], file_path
        )
    return result


def is_public_function(function: Function):
    if function['meta']['access'] and function['meta']['access'] == 'private':
        return False
    return True


def parse_function(function: Function, funct_file_path, file_path):
    signature = (
        minihtml.span_wrap(function['name'], 'entity.name.function')
        + '('
        + ('...' if function['meta']['parameters'] else '')
        + ')'
    )
    if function['meta']['returntype']:
        signature += ': ' + minihtml.span_wrap(
            function['meta']['returntype'], 'storage.type'
        )
    header = minihtml.link(function['name'], signature, plain=True)

    body = ''
    if funct_file_path != file_path:
        body += ' ' + minihtml.note('from ' + funct_file_path.split('/')[-1])
    if 'hint' in function['meta'] and function['meta']['hint']:
        body += minihtml.block(minihtml.escape_text(function['meta']['hint']))

    arguments = []
    for arg in function['meta']['parameters']:
        default = ''
        if arg['default']:
            default = minihtml.labeled(
                'Default', minihtml.code(minihtml.escape_text(arg['default']))
            )
        hint = minihtml.escape_text(arg.get('hint') or '')
        arguments.append(
            minihtml.lines(
                [minihtml.signature(minihtml.param_header(arg)), default, hint]
            )
        )

    if len(arguments) > 0:
        body += minihtml.bullets(arguments)

    return header, body


def parse_properties(file_path, metadata: ExtendedMetadata):
    properties = metadata['properties']
    property_file_map = metadata['property_file_map']
    sorted_properties = [
        (properties[key], property_file_map[key]) for key in sorted(properties)
    ]
    return [
        parse_property(prop, prop_file_path, file_path)
        for prop, prop_file_path in sorted_properties
    ]


def parse_property(prop: Property, prop_file_path, file_path):
    header = minihtml.header(prop['name'], prop['meta']['type'], 'storage.type')
    if prop_file_path != file_path:
        header += ' ' + minihtml.note('from ' + prop_file_path.split('/')[-1])

    accessors = [key for key in ['setter', 'getter'] if prop['meta'][key]]
    inject = prop['meta'].get('inject')
    body = minihtml.lines(
        [
            minihtml.labeled('Accessors', ', '.join(accessors)) if accessors else '',
            minihtml.labeled('Inject', minihtml.escape_text(inject)) if inject else '',
        ]
    )
    return header, body


def get_function_region(view, function_name):
    functions = view.find_by_selector('entity.name.function -meta.function.body')
    for funct_region in functions:
        if view.substr(funct_region).lower() == function_name:
            pt = funct_region.begin()
            break
    else:
        return None

    if view.match_selector(pt, 'meta.function.cfml'):
        # tag function: the opening tag, the body and the closing tag
        regions = adjacent_scope_regions(
            view,
            pt,
            'meta.function.cfml',
            'meta.function.body.tag.cfml',
            'meta.tag.cfml',
        )
    else:
        # script function: the declaration and the body
        regions = adjacent_scope_regions(
            view, pt, 'meta.function.declaration.cfml', 'meta.function.body.cfml'
        )
    if regions is None:
        return None
    return sublime.Region(regions[0].begin(), regions[-1].end())


def adjacent_scope_regions(view, pt, *scopes):
    """
    Returns the regions of scopes that follow each other, the first at pt,
    each next one right after the previous, or None when one is missing,
    as when a tag function is not closed.
    """
    regions = []
    for scope in scopes:
        region = utils.get_scope_region_containing_point(view, pt, scope)
        if region is None:
            return None
        regions.append(region)
        pt = region.end() + 1
    return regions
