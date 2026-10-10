import sublime
from typing import NamedTuple, TypedDict
from .. import kinds
from ..component_parser.metadata import (
    ExtendedMetadata,
    Function,
    Parameter,
    parameter_label,
)


class CfcCompletion(NamedTuple):
    """
    The completion of a method. Providers filter these on accessor and private
    and turn them into CompletionItems with to_completion_item().
    """

    name: str
    returntype: str
    # a snippet
    content: str
    # of the component that declares the method
    file_path: str
    # whether the method is an accessor generated for a property
    accessor: bool
    private: bool


class TypeCompletions(TypedDict):
    # of the init method, or of the component's initmethod, if it has one
    constructor: CfcCompletion | None
    # of every method, in the order of their names
    functions: list[CfcCompletion]


# the completions of a component for each value of the cfml_cfc_completions
# setting: "basic", "required" and "full"
FileCompletions = dict[str, TypeCompletions]


# the completions of the methods of the components of an index, by the file
# that declares the method, the method's lower case name and the completion
# type; an inherited method is in the completions of every component that
# inherits it, and is made once
CompletionCache = dict[tuple[str, str, str], CfcCompletion]


def build(file_paths, get_extended_metadata) -> dict[str, FileCompletions]:
    completions = {}
    cache: CompletionCache = {}
    for file_path in file_paths:
        extended_metadata = get_extended_metadata(file_path)
        completions[file_path] = build_file_completions(extended_metadata, cache)
    return completions


def build_file_completions(
    extended_metadata: ExtendedMetadata, cache: CompletionCache | None = None
) -> FileCompletions:
    """
    Returns the completions of a component. A cache is shared by components
    of one index, where a method of a file is the same in each of them.
    """
    file_completions = {}
    constructor = (extended_metadata['initmethod'] or 'init').lower()
    for completion_type in ['basic', 'required', 'full']:
        comps: TypeCompletions = {
            'constructor': None,
            'functions': make_completions(
                extended_metadata['functions'],
                extended_metadata['function_file_map'],
                completion_type,
                cache,
            ),
        }

        if constructor in extended_metadata['functions']:
            constructor_meta = extended_metadata['functions'][constructor]
            constructor_loc = extended_metadata['function_file_map'][constructor]
            comps['constructor'] = make_completion(
                constructor_meta, constructor_loc, completion_type
            )

        file_completions[completion_type] = comps

    return file_completions


def make_completions(
    funct_meta: dict[str, Function],
    funct_cfcs: dict[str, str],
    completion_type,
    cache: CompletionCache | None = None,
):
    if cache is None:
        return [
            make_completion(
                funct_meta[funct_key], funct_cfcs[funct_key], completion_type
            )
            for funct_key in sorted(funct_meta)
        ]

    completions = []
    for funct_key in sorted(funct_meta):
        key = (funct_cfcs[funct_key], funct_key, completion_type)
        completion = cache.get(key)
        if completion is None:
            completion = cache[key] = make_completion(
                funct_meta[funct_key], funct_cfcs[funct_key], completion_type
            )
        completions.append(completion)
    return completions


def make_completion(funct: Function, cfc_file_path, completion_type):
    return CfcCompletion(
        funct['name'],
        funct['meta']['returntype'] or '',
        escape_snippet_text(funct['name'])
        + '('
        + make_arguments_string(funct['meta']['parameters'], completion_type)
        + ')',
        cfc_file_path,
        funct['implicit'],
        funct['meta']['access'] == 'private',
    )


def escape_snippet_text(text):
    # outside a snippet field only \ and $ are special: a method named
    # $fixNumber was read as a snippet variable
    return text.replace('\\', '\\\\').replace('$', '\\$')


def to_completion_item(completion: CfcCompletion, annotation: str | None = None):
    # details name the component that declares the method; the annotation
    # is the return type unless it is given
    return sublime.CompletionItem(
        completion.name,
        completion.returntype if annotation is None else annotation,
        completion.content,
        sublime.CompletionFormat.SNIPPET,
        kind=kinds.METHOD,
        details=completion.file_path.split('/').pop().split('.')[0],
    )


def make_arguments_string(parameters: list[Parameter], completion_type):
    index = 1
    delim = ''
    arguments_string = ''

    if completion_type == 'basic':
        return arguments_string

    for argument_params in parameters:
        if not argument_params:
            continue
        if argument_params['required'] or index == 1:
            arguments_string += (
                delim
                + '${'
                + str(index)
                + ':'
                + make_argument_string(argument_params, completion_type)
                + '}'
            )
            index += 1
        elif completion_type == 'required':
            break
        else:
            arguments_string += (
                '${'
                + str(index)
                + ':, ${'
                + str(index + 1)
                + ':'
                + make_argument_string(argument_params, completion_type)
                + '}}'
            )
            index += 2
        delim = ', '
    return arguments_string


def make_argument_string(argument_params: Parameter, completion_type):
    if completion_type == 'required':
        argument_string = parameter_label(argument_params)
    else:
        argument_string = 'required ' if argument_params['required'] else ''
        if argument_params['type']:
            argument_string += argument_params['type'] + ' '
        argument_string += parameter_label(argument_params)
        if argument_params['default']:
            argument_string += '=' + argument_params['default']

    # the string fills a snippet field, where \, $ and } are special: a
    # struct default, {a: 1}, or a $ in a name or default broke the snippet
    for char in '\\$}':
        argument_string = argument_string.replace(char, '\\' + char)
    return argument_string
