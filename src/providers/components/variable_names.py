import sublime
from ... import utils
from ...component_reference import ComponentReference
from . import cfcs, inject


def get_dot_completions(cfml_view):
    if not cfml_view.project_name or len(cfml_view.dot_context) == 0:
        return None

    # a known cfc name, a getter for one, or an injected property
    found = find_receiver(cfml_view, cfml_view.dot_context)
    if found and found[0]:
        return cfcs.get_completions(cfml_view.project_name, found[0])

    return None


def find_call_cfc(cfml_view):
    """
    Returns a ComponentReference to the cfc that the method call the view's
    position is in is called on, or None.
    """
    function_call_params = cfml_view.function_call_params
    found = find_receiver(
        cfml_view, function_call_params.dot_context, function_call_params.function_name
    )
    if found:
        cfc_infos, region = found
        return get_reference(cfc_infos, None, [region])

    return None


def find_receiver(cfml_view, dot_context, function_name=None):
    """
    Returns the components that what a dot context ends in could be, best
    first, with the region of its name, or None when it names nothing: a
    property of the component in the view that has an inject attribute is
    what the attribute asks for, and nothing else when that is not known;
    otherwise a variable name, or a getter for one, is looked up. The
    components that have the method called, if any has it, are kept.
    """
    project_name = cfml_view.project_name
    if not project_name:
        return None
    from_file = get_file_path(cfml_view)
    injected = find_injected_property(cfml_view, dot_context)
    if injected:
        prop, region = injected
        return lookup_injected(project_name, prop, from_file, function_name), region

    found = cfcs.find_cfc_in_dot_context(project_name, dot_context)
    if found:
        cfc_infos = cfcs.lookup(project_name, [found[0]], from_file, function_name)
        return cfc_infos, found[1]

    return None


def find_injected_property(cfml_view, dot_context):
    """
    Returns the property of the component in the view that a dot context is,
    `name` or `variables.name`, with the region of its name, when the
    property has an inject attribute; the component's own and inherited
    properties are looked at.
    """
    if not 0 < len(dot_context) <= 2 or any(s.is_function for s in dot_context):
        return None
    if len(dot_context) == 2 and dot_context[1].name.lower() != 'variables':
        return None
    prop = get_injected_property(cfml_view, dot_context[0].name)
    if prop:
        return prop, dot_context[0].name_region
    return None


def get_injected_property(cfml_view, name):
    prop = cfml_view.view_metadata['properties'].get(name.lower())
    if prop and prop['meta'].get('inject') is not None:
        return prop
    return None


def lookup_injected(
    project_name, prop, from_file=None, function_name=None
) -> list[cfcs.CfcInfo]:
    """
    Returns the components that an injected property could be, best first:
    the bean the attribute names, then the property's own name, each looked
    up as a variable name. A framework DSL is the class the table of DSLs
    gives it, and no component when the table does not have it: the name
    of the property is not looked up, as `log` would find a handler named
    Log. What a method of a bean returns is not known.
    """
    injection = inject.parse(prop['meta']['inject'], prop['name'])
    if injection.bean_name:
        return cfcs.lookup(
            project_name,
            [injection.bean_name, prop['name']],
            from_file,
            function_name,
        )
    if injection.dsl:
        class_path = inject.find_class(injection.dsl)
        if class_path:
            return cfcs.lookup_class(project_name, class_path, function_name)
    return []


def get_file_path(cfml_view):
    # the file the name is written in, which candidates are ranked from
    return getattr(cfml_view, 'file_path', None)


def get_reference(cfc_infos, function_name, regions):
    """
    Returns a ComponentReference to the best of the components a name is
    given to, with the others as its candidates, or None when there are
    none.
    """
    if not cfc_infos:
        return None
    best = cfc_infos[0]
    return ComponentReference(
        best.file_path,
        best.name,
        function_name,
        regions,
        candidates=tuple(cfc_info.file_path for cfc_info in cfc_infos[1:]),
        guessed=best.guessed,
    )


def find_cfc(cfml_view):
    """
    Returns a ComponentReference to the cfc, or the method of one, that the
    view's position is on, or None.
    """
    project_name = cfml_view.project_name
    if not project_name:
        return None

    if cfml_view.view.match_selector(cfml_view.position, 'meta.function-call.method'):
        function_name, function_name_region, function_args_region = (
            cfml_view.get_function_call(cfml_view.position)
        )
        region = sublime.Region(
            function_name_region.begin(), function_args_region.end()
        )
        if cfml_view.view.substr(function_name_region.begin() - 1) == '.':
            dot_context = cfml_view.get_dot_context(function_name_region.begin() - 1)
            # the components that have the method, if any has it
            found = find_receiver(cfml_view, dot_context, function_name)
            if found:
                cfc_infos, cfc_name_region = found
                if cfc_infos and cfcs.has_method(
                    project_name, cfc_infos[0].file_path, function_name
                ):
                    return get_reference(
                        cfc_infos, function_name, [region, cfc_name_region]
                    )

    # check for cfc
    cfc_name = None
    cfc_name_region = None
    check_position = cfml_view.position
    if cfml_view.view.match_selector(cfml_view.position, 'punctuation.accessor.cfml'):
        check_position = cfml_view.position + 1
    if cfml_view.view.match_selector(check_position, 'variable.other'):
        # we need to find the whole dot context now in order to search for variable names that contain dots
        dot_context = get_dot_context(cfml_view, check_position)
        injected = find_injected_property(cfml_view, dot_context)
        if injected and injected[1].contains(cfml_view.position):
            cfc_infos = lookup_injected(
                project_name, injected[0], get_file_path(cfml_view)
            )
            return get_reference(cfc_infos, None, [injected[1]])
        found = cfcs.search_dot_context_for_cfc(project_name, dot_context)
        if found and found[1].contains(cfml_view.position):
            cfc_name, cfc_name_region = found
    elif cfml_view.view.match_selector(
        cfml_view.position, 'meta.tag.property.name.cfml'
    ):
        cfc_name_region = cfml_view.view.word(cfml_view.position)
        cfc_name = cfml_view.view.substr(cfc_name_region).lower()
        # the declaration of an injected property
        prop = get_injected_property(cfml_view, cfc_name)
        if prop:
            cfc_infos = lookup_injected(project_name, prop, get_file_path(cfml_view))
            return get_reference(cfc_infos, None, [cfc_name_region])
    elif cfml_view.view.match_selector(
        cfml_view.position, 'meta.function-call.cfml variable.function.cfml'
    ):
        cfc_name_region = cfml_view.view.word(cfml_view.position)
        var_name = cfml_view.view.substr(cfc_name_region).lower()
        if var_name.startswith('get'):
            cfc_name = var_name[3:]

    if cfc_name and cfc_name_region:
        cfc_infos = cfcs.lookup(project_name, [cfc_name], get_file_path(cfml_view))
        return get_reference(cfc_infos, None, [cfc_name_region])

    return None


def get_dot_context(cfml_view, position):
    current_element = cfml_view.view.word(position)
    next_pt = utils.get_next_character(cfml_view.view, current_element.end())

    if cfml_view.view.match_selector(
        next_pt, 'punctuation.accessor.cfml'
    ) and cfml_view.view.match_selector(next_pt + 1, 'variable.other'):
        return get_dot_context(cfml_view, next_pt + 1)

    dot_context = [
        utils.Symbol(
            cfml_view.view.substr(current_element), False, None, None, current_element
        )
    ]
    dot_context.extend(cfml_view.get_dot_context(current_element.begin() - 1))
    return dot_context
