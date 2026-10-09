import sublime
from functools import partial
from typing import NamedTuple
from . import minihtml, project_files, utils
from .project_watcher import project_watcher
from .cfml_view import (
    CompletionDoc,
    Documentation,
    GotoCfmlFile,
    GotoChoice,
    MethodPreview,
)
from .component_index import component_index, documentation

PRIORITY = 2


class ComponentReference(NamedTuple):
    """
    A component that a provider found at a position in a view, by a variable
    name, a dot path or an entity name, or the method called on it when
    function_name is set. The functions below build what the providers return
    for one from the component index.
    """

    file_path: str
    # the name the docs show for the component, if any
    class_name: str | None
    # in lower case, as the metadata is keyed; the component need not have
    # a method of that name
    function_name: str | None
    # what the reference covers in the view
    regions: list[sublime.Region]
    # the component's name in the docs of its methods, when that differs
    method_class_name: str | None = None
    # the other components that the name could be, best first; file_path is
    # the best of all
    candidates: tuple[str, ...] = ()
    # whether the component was found by its name alone
    guessed: bool = False


def get_metadata(cfml_view, reference):
    return component_index.get_extended_metadata_by_file_path(
        cfml_view.project_name, reference.file_path
    )


def has_method(cfml_view, reference):
    """Returns whether the component has the method the reference is to."""
    metadata = get_metadata(cfml_view, reference)
    return metadata is not None and reference.function_name in metadata['functions']


def get_cached_method_preview(cfml_view, metadata, function_name):
    function_file_path = metadata['function_file_map'][function_name]
    cache = component_index.get_cache_by_file_path(
        cfml_view.project_name, function_file_path
    )
    # the file has left the index since the metadata was read
    if cache is None:
        return None
    return documentation.cached_method_preview(
        cfml_view.view, cache, function_file_path, function_name
    )


def tell_apart(file_paths):
    """
    Returns the end of each component file's path that tells it from the
    others: its folder and name, and as few more folders as it takes. The
    same as cfcs.tell_apart(), which this module cannot import, as the
    providers' package imports this one.
    """
    parts = [file_path[:-4].split('/') for file_path in file_paths]
    for count in range(2, max(len(p) for p in parts)):
        ends = ['/'.join(p[-count:]) for p in parts]
        if len({end.lower() for end in ends}) == len(ends):
            return ends
    return [file_path[:-4] for file_path in file_paths]


def get_candidates_note(reference):
    labels = []
    if reference.candidates:
        labels = tell_apart([reference.file_path, *reference.candidates])[1:]
    return documentation.build_candidates_note(reference.guessed, labels)


def on_navigate(cfml_view, reference, function_name, on_navigate, href):
    """
    Opens the candidate that a link of the doc is to, at the method the doc
    is for, if any; other links are for the doc's own on_navigate.
    """
    index = documentation.candidate_index(href)
    if index is None:
        on_navigate(href)
        return

    file_path = reference.candidates[index]
    target = get_goto_target(cfml_view, file_path, function_name)
    window = cfml_view.view.window()
    if target is not None and target[1]:
        window.run_command(
            'cfml_navigate_to_method', {'file_path': target[0], 'href': target[1]}
        )
    else:
        window.open_file(file_path)


def get_inline_documentation(cfml_view, reference):
    """
    Returns the documentation of the method when the component has it, and
    of the component otherwise; None for a component that is not indexed.
    A component found by its name alone, or that could be another, says so.
    """
    metadata = get_metadata(cfml_view, reference)
    if metadata is None:
        return None

    note = get_candidates_note(reference)
    function_name = reference.function_name
    if function_name in metadata['functions']:
        method_preview = None
        if utils.get_setting('cfml_doc_method_preview'):
            method_preview = get_cached_method_preview(
                cfml_view, metadata, function_name
            )
        doc, callback = documentation.get_method_documentation(
            cfml_view.view,
            metadata,
            reference.file_path,
            function_name,
            reference.method_class_name or reference.class_name,
            metadata['functions'][function_name]['name'],
            method_preview,
            note,
            folders=get_project_folders(cfml_view),
        )
    else:
        function_name = None
        doc, callback = documentation.get_documentation(
            cfml_view.view,
            metadata,
            reference.file_path,
            reference.class_name,
            note,
            folders=get_project_folders(cfml_view),
        )

    if reference.candidates:
        callback = partial(on_navigate, cfml_view, reference, function_name, callback)

    return Documentation(reference.regions, doc, callback, PRIORITY)


def get_method_preview(cfml_view, reference):
    metadata = get_metadata(cfml_view, reference)
    function_name = reference.function_name
    if metadata is None or function_name not in metadata['functions']:
        return None

    method_preview = get_cached_method_preview(cfml_view, metadata, function_name)
    if method_preview is None:
        return None

    doc, callback = documentation.get_method_preview(
        cfml_view.view,
        metadata,
        reference.file_path,
        function_name,
        method_preview,
        folders=get_project_folders(cfml_view),
    )
    return MethodPreview(reference.regions, doc, callback, PRIORITY)


def get_goto_target(cfml_view, file_path, function_name):
    """
    Returns the file and symbol that a goto to the component, or to its
    method when function_name is set, opens: for an inherited method, the
    component that declares it. None when the component lacks the method.
    """
    if not function_name:
        return file_path, None

    metadata = component_index.get_extended_metadata_by_file_path(
        cfml_view.project_name, file_path
    )
    if metadata is None or function_name not in metadata['functions']:
        return None

    return (
        metadata['function_file_map'][function_name],
        metadata['functions'][function_name]['name'],
    )


def get_goto_cfml_file(cfml_view, reference):
    """
    Returns the component's file, or for a method the file that declares
    it, which is a component it extends for an inherited method. When the
    reference has other candidates, the goto offers them too.
    """
    target = get_goto_target(cfml_view, reference.file_path, reference.function_name)
    if target is None:
        return None
    return GotoCfmlFile(*target, PRIORITY, get_goto_choices(cfml_view, reference))


def get_project_folders(cfml_view):
    """Returns the folders of the project that paths are shown relative to."""
    return project_watcher.get_project_folders(cfml_view.project_name)


def get_goto_choices(cfml_view, reference):
    """
    Returns what a goto to the reference can open, the best candidate
    first: empty when that is one file. Candidates that lead to the same
    place, as a method they inherit from one component, are one choice,
    and one that lacks the method is left out.
    """
    if not reference.candidates:
        return ()

    folders = get_project_folders(cfml_view)
    choices = []
    targets = set()
    for file_path in (reference.file_path, *reference.candidates):
        target = get_goto_target(cfml_view, file_path, reference.function_name)
        if target is None or target in targets:
            continue
        targets.add(target)
        details = ''
        if target[0] != file_path:
            details = 'inherited from ' + minihtml.escape_text(
                project_files.display_path(folders, target[0])
            )
        label = project_files.display_path(folders, file_path)
        choices.append(GotoChoice(label, details, *target))

    return tuple(choices) if len(choices) > 1 else ()


def get_completion_doc(cfml_view, reference):
    """
    Returns the doc of the arguments of the method call that the view's
    position is in, a call of a method of the component.
    """
    function_call_params = cfml_view.function_call_params
    function_name = function_call_params.function_name
    metadata = get_metadata(cfml_view, reference)
    if metadata is None or function_name not in metadata['functions']:
        return None

    doc, callback = documentation.get_function_call_params_doc(
        metadata,
        function_call_params,
        reference.method_class_name or reference.class_name,
        metadata['functions'][function_name]['name'],
    )
    return CompletionDoc(None, doc, callback, PRIORITY)
