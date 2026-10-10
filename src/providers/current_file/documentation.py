import sublime
from functools import partial
from typing import NamedTuple
from ... import component_reference
from ... import utils
from ...cfml_view import CompletionDoc, Documentation, GotoCfmlFile, MethodPreview
from ...component_index import component_index
from ...component_index import documentation as component_documentation
from ...component_parser import ExtendedMetadata
from ...component_reference import ComponentReference
from ...project_watcher import project_watcher


class FunctionInfo(NamedTuple):
    """A function of the component in the view, or one that it inherits."""

    extended_meta: ExtendedMetadata
    function_name: str
    header: str
    regions: list[sublime.Region]


class CfcInfo(NamedTuple):
    """The component in the view, or the one it extends."""

    extended_meta: ExtendedMetadata
    file_path: str
    header: str
    regions: list[sublime.Region]


def get_inline_documentation(cfml_view, doc_type):
    function_info = get_function_info(cfml_view, cfml_view.position)
    if function_info:
        return get_function_documentation(cfml_view, function_info)

    cfc_info = get_cfc_info(cfml_view, cfml_view.position)
    if cfc_info:
        doc, callback = get_documentation(
            cfml_view.view,
            cfc_info.extended_meta,
            cfc_info.file_path,
            cfc_info.header,
            project_watcher.get_project_folders(cfml_view.project_name),
        )
        return Documentation(cfc_info.regions, doc, callback, 2)

    return None


def get_method_preview(cfml_view):
    function_info = get_function_info(cfml_view, cfml_view.position)
    if not function_info:
        return None

    extended_meta, function_name, header, regions = function_info
    inherited = get_inherited_reference(cfml_view, function_info)
    if inherited:
        return component_reference.get_method_preview(cfml_view, inherited)

    function_preview = component_documentation.build_method_preview(
        cfml_view.view, function_name
    )
    doc = component_documentation.build_method_preview_doc(
        extended_meta,
        function_name,
        function_preview,
        folders=project_watcher.get_project_folders(cfml_view.project_name),
    )
    callback = partial(
        on_navigate,
        cfml_view.view,
        extended_meta['function_file_map'][function_name],
        extended_meta['function_file_map'],
    )
    return MethodPreview(regions, doc, callback, 2)


def get_goto_cfml_file(cfml_view):
    function_info = get_function_info(cfml_view, cfml_view.position)
    if function_info:
        extended_meta, function_name, header, regions = function_info
        return GotoCfmlFile(
            extended_meta['function_file_map'][function_name],
            extended_meta['functions'][function_name]['name'],
            2,
        )

    cfc_info = get_cfc_info(cfml_view, cfml_view.position)
    if cfc_info:
        return GotoCfmlFile(cfc_info.file_path, None, 2)

    return None


def get_completion_docs(cfml_view):
    if cfml_view.function_call_params and not cfml_view.function_call_params.support:
        header = get_function_call_params_header(cfml_view)

        if header:
            model_doc = component_documentation.build_function_call_params_doc(
                cfml_view.view_metadata, cfml_view.function_call_params, None, header
            )
            return CompletionDoc(None, model_doc, None, 2)

    return None


def get_function_info(cfml_view, pt):
    if cfml_view.view.match_selector(pt, 'meta.function-call.cfml'):
        function_name, function_name_region, function_args_region = (
            cfml_view.get_function_call(pt)
        )
        if function_name in cfml_view.view_metadata['functions']:
            header = cfml_view.view_metadata['functions'][function_name]['name']
            region = sublime.Region(
                function_name_region.begin(), function_args_region.end()
            )
            return FunctionInfo(
                cfml_view.view_metadata, function_name, header, [region]
            )

    if cfml_view.view.match_selector(pt, 'meta.function-call.method.cfml'):
        function_name, function_name_region, function_args_region = (
            cfml_view.get_function_call(pt)
        )
        region = sublime.Region(
            function_name_region.begin(), function_args_region.end()
        )
        if cfml_view.view.substr(function_name_region.begin() - 1) == '.':
            dot_context = cfml_view.get_dot_context(function_name_region.begin() - 1)

            if dot_context[0].name in ['this', 'super']:
                if function_name in cfml_view.view_metadata['functions']:
                    header = cfml_view.view_metadata['functions'][function_name]['name']
                    return FunctionInfo(
                        cfml_view.view_metadata,
                        function_name,
                        header,
                        [region, dot_context[0].name_region],
                    )

    return None


def get_function_call_params_header(cfml_view):
    if not cfml_view.function_call_params.method:
        if (
            cfml_view.function_call_params.function_name
            in cfml_view.view_metadata['functions']
        ):
            return cfml_view.view_metadata['functions'][
                cfml_view.function_call_params.function_name
            ]['name']
    else:
        if cfml_view.function_call_params.dot_context[0].name == 'this':
            if (
                cfml_view.function_call_params.function_name
                in cfml_view.view_metadata['functions']
            ):
                return cfml_view.view_metadata['functions'][
                    cfml_view.function_call_params.function_name
                ]['name']

        if cfml_view.function_call_params.dot_context[0].name == 'super':
            if (
                cfml_view.view_metadata
                and cfml_view.function_call_params.function_name
                in cfml_view.view_metadata['functions']
            ):
                return cfml_view.view_metadata['functions'][
                    cfml_view.function_call_params.function_name
                ]['name']

    return None


def get_cfc_info(cfml_view, pt):
    file_path = cfml_view.file_path or ''

    if cfml_view.view.match_selector(pt, 'variable.language.this.cfml'):
        return CfcInfo(
            cfml_view.view_metadata, file_path, 'this', [cfml_view.view.word(pt)]
        )

    if cfml_view.view.match_selector(pt, 'variable.language.super.cfml'):
        extends_file_path = component_index.resolve_path(
            cfml_view.project_name, file_path, cfml_view.view_metadata['extends']
        )
        extended_meta = component_index.get_extended_metadata_by_file_path(
            cfml_view.project_name, extends_file_path
        )
        if extended_meta and extends_file_path:
            return CfcInfo(
                extended_meta,
                extends_file_path,
                cfml_view.view_metadata['extends'],
                [cfml_view.view.word(pt)],
            )

    return None


def get_inherited_reference(cfml_view, function_info):
    """
    Returns a ComponentReference to a function that the component in the
    view inherits, in the component that declares it, or None for a
    function of its own.
    """
    function_name = function_info.function_name
    function_file_path = function_info.extended_meta['function_file_map'][function_name]
    if len(function_file_path) > 0 and function_file_path != (
        cfml_view.file_path or ''
    ):
        return ComponentReference(
            function_file_path, None, function_name, function_info.regions
        )
    return None


def on_navigate(view, file_path, function_file_map, href):

    if href == '__go_to_component':
        view.window().open_file(file_path)
    else:
        file_path = function_file_map[href.lower()]
        view.hide_popup()
        view.window().run_command(
            'cfml_navigate_to_method', {'file_path': file_path, 'href': href}
        )


def get_documentation(view, extended_meta, file_path, header, folders):
    model_doc = component_documentation.build_documentation(
        extended_meta, file_path, header, folders=folders
    )
    callback = partial(on_navigate, view, file_path, extended_meta['function_file_map'])
    return model_doc, callback


def get_function_documentation(cfml_view, function_info):
    inherited = get_inherited_reference(cfml_view, function_info)
    if inherited:
        return component_reference.get_inline_documentation(cfml_view, inherited)

    extended_meta, function_name, header, regions = function_info
    function_preview = None
    if utils.get_setting('cfml_doc_method_preview'):
        function_preview = component_documentation.build_method_preview(
            cfml_view.view, function_name
        )
    model_doc = component_documentation.build_method_documentation(
        extended_meta,
        function_name,
        None,
        header,
        function_preview,
        folders=project_watcher.get_project_folders(cfml_view.project_name),
    )
    callback = partial(
        on_navigate,
        cfml_view.view,
        extended_meta['function_file_map'][function_name],
        extended_meta['function_file_map'],
    )
    return Documentation(regions, model_doc, callback, 2)
