import contextlib
import sublime
import os
import shutil
from dataclasses import dataclass
from typing import Any, TypedDict
from ..project_files import Discovery
from ..project_index import ProjectIndex, Scan
from ..project_watcher import project_watcher
from .. import project_files
from .. import utils
from .. import component_parser
from ..component_parser import ComponentMetadata, ExtendedMetadata
from . import completions
from . import dot_paths


class DotPath(TypedDict):
    file_path: str
    # as it is cased in the file system
    dot_path: str


class Entity(TypedDict):
    file_path: str
    entity_name: str


class ComponentProjectData(TypedDict):
    """The components of a project and what is derived from them."""

    # the metadata of each component file, by path
    index: dict[str, ComponentMetadata]
    # the path of each component file, by lower case path
    file_paths: dict[str, str]
    # by lower case dot path
    dot_paths: dict[str, DotPath]
    # by lower case entity name
    entities: dict[str, Entity]
    # the method previews of each file, filled in as they are built
    cache: dict[str, dict[str, Any]]
    # the completions of each file, by path
    completions: dict[str, completions.FileCompletions]
    # whether the components were found in the folders of the window, rather
    # than in the project's cfc_folders
    automatic: bool
    # how the components of each folder of the window were found, by folder;
    # empty unless automatic
    discoveries: dict[str, Discovery]
    # the folders that box.json files install dependencies into, over all
    # the discoveries, sorted; empty unless automatic
    install_paths: list[str]
    # the files whose folder chain, relative to the folder of the window or
    # the parent of the install path or cfc folder that they are found from,
    # ends in each lower case dot path; see dot_paths.py
    file_suffixes: dict[str, list[str]]
    # the same for the folders that hold the files
    folder_suffixes: dict[str, list[str]]


# the cfml_index_max_files setting when it is not a positive number
DEFAULT_MAX_FILES = 5000


@dataclass(frozen=True)
class AutoScope:
    """
    The scope of a project whose components are found in the folders of its
    window, with project_files.discover().
    """

    folders: tuple[str, ...]
    # the most component files a folder can have to be indexed
    max_files: int


def get_max_files(project_data) -> int:
    max_files = utils.get_project_data_setting(project_data, 'cfml_index_max_files')
    if isinstance(max_files, int) and not isinstance(max_files, bool) and max_files > 0:
        return max_files
    return DEFAULT_MAX_FILES


def is_worth_describing(discovery: Discovery) -> bool:
    """
    Returns whether the console tells of the discovery of a folder: not when
    it found no component files, or the folder has nothing of CFML, since
    every window with a folder is looked at.
    """
    if discovery.reason is None:
        return len(discovery.files) > 0
    return discovery.reason != project_files.NO_MARKER


def describe_discovery(folder, discovery: Discovery) -> str:
    """Returns what the console says about the discovery of a folder."""
    if discovery.reason is not None:
        source = '' if discovery.source == 'none' else ' (' + discovery.source + ')'
        return f"CFML: not indexing '{folder}'{source} - {discovery.reason}"
    message = f"CFML: found {len(discovery.files)} component files in '{folder}' ({discovery.source}"
    if discovery.install_paths:
        installed = sum(
            1
            for file_path in discovery.files
            if any(
                project_files.is_under(install_path, file_path)
                for install_path in discovery.install_paths
            )
        )
        count = len(discovery.install_paths)
        message += f', {installed} of them in {count} install path' + (
            's' if count != 1 else ''
        )
    return message + ')'


def build_dot_paths(path_index, mappings, base_dir) -> dict[str, DotPath]:
    dot_paths = {}
    for file_path in path_index:
        for mapping in mappings:
            normalized_mapping = utils.normalize_mapping(mapping, base_dir)
            path_parts = utils.get_mapped_path_parts(file_path, normalized_mapping)
            if path_parts:
                dot_path = '.'.join(path_parts)[:-4]
                dot_paths[dot_path.lower()] = {
                    'file_path': file_path,
                    'dot_path': dot_path,
                }
    return dot_paths


def build_entities(path_index: dict[str, ComponentMetadata]) -> dict[str, Entity]:
    entities = {}
    for file_path, metadata in path_index.items():
        if not metadata['persistent']:
            continue
        cfc_path, file_ext = os.path.splitext(file_path)
        cfc_name = cfc_path.split('/').pop()
        entity_name = metadata['entityname'] if metadata['entityname'] else cfc_name
        entities[entity_name.lower()] = {
            'file_path': file_path,
            'entity_name': entity_name,
        }
    return entities


def move_legacy_cache(cache_path):
    # older versions kept the cache in Packages/User/CFML
    legacy_dir = os.path.join(sublime.packages_path(), 'User', 'CFML')
    legacy_path = os.path.join(legacy_dir, 'cfc_index_cache.sqlite')
    if not os.path.isfile(legacy_path):
        return
    try:
        if os.path.exists(cache_path):
            os.remove(legacy_path)
        else:
            shutil.move(legacy_path, cache_path)
    except OSError as e:
        print('CFML: unable to move the legacy component index cache - ' + str(e))
        return
    # the folder stays if anything else is in it
    with contextlib.suppress(OSError):
        os.rmdir(legacy_dir)


class ComponentIndex(ProjectIndex[ComponentProjectData]):
    label = 'components'

    def __init__(self):
        super().__init__('cfc_folders')
        self.parser: component_parser.Parser | None = None

    def init_parser(self):
        # the index cache is derived data, so keep it out of Packages/User
        cache_dir = os.path.normpath(
            os.path.join(sublime.cache_path(), '..', 'Package Storage', 'CFML')
        )
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, 'cfc_index_cache.sqlite')
        move_legacy_cache(cache_path)
        self.parser = component_parser.Parser(cache_path)

    def clear_cache(self):
        """
        Empties the parser's cache and indexes the open projects again, with
        every file parsed again. It runs where the projects are indexed, so
        not while one is.
        """
        sublime.set_timeout_async(self.clear_cache_and_reindex)

    def clear_cache_and_reindex(self):
        if self.parser is None:
            # it did not start, and the console has the reason
            print('CFML: the component index cache is not available')
            return
        self.parser.clear_cache()
        print('CFML: component index cache cleared')
        for project_name in list(project_watcher.projects):
            self.reindex_project(project_name)

    def get_scope(self, project_name):
        """
        A project with cfc_folders in its project file indexes those folders,
        and nothing when the list is empty. Any other project indexes the
        folders of its window when cfml_auto_index is on.
        """
        project = self.get_project(project_name)
        if project is None:
            return None
        if 'cfc_folders' in project.data:
            return super().get_scope(project_name)
        if not project.folders or not utils.get_project_data_setting(
            project.data, 'cfml_auto_index'
        ):
            return None
        return AutoScope(project.folders, get_max_files(project.data))

    def scan(self, project_name, scope):
        if not isinstance(scope, AutoScope):
            return super().scan(project_name, scope)
        if self.parser is None:
            # it did not start, and the console has the reason
            return Scan({}, {})

        discoveries = {}
        file_paths = {}
        for folder in scope.folders:
            discovery = project_files.discover(folder, scope.max_files)
            discoveries[folder] = discovery
            # a folder inside another one of the window lists its files again
            file_paths.update(dict.fromkeys(discovery.files))
        return Scan(self.parser.parse_files(file_paths), discoveries)

    def is_quiet_when_empty(self, scope):
        # most windows with a folder have nothing to index
        return isinstance(scope, AutoScope)

    def describe_scan(self, scan):
        if not isinstance(scan.sources, dict):
            return []
        return [
            describe_discovery(folder, discovery)
            for folder, discovery in scan.sources.items()
            if is_worth_describing(discovery)
        ]

    def belongs(self, project_name, file_path):
        """
        A saved component file belongs to a project whose components are
        found in the folders of its window when it is in the index, or when
        the discovery of one of the folders covers it: it is under an install
        path, or not ignored by git, and the folder is not over the cap.
        """
        if not isinstance(self.scopes.get(project_name), AutoScope):
            return super().belongs(project_name, file_path)
        if not self.accepts_file(file_path):
            return False
        project_data = self.data.get(project_name)
        if project_data is None:
            return False
        if file_path in project_data['index']:
            return True
        return any(
            project_files.covers(folder, discovery, file_path)
            for folder, discovery in project_data['discoveries'].items()
        )

    def project_event_handler(self, event, project_name, file_path=None):
        if event in (
            'project_file_updated',
            'project_file_removed',
        ) and self.is_box_file(project_name, file_path):
            # only a new discovery reads the install paths and the markers
            self.reindex_project(project_name)
            return
        super().project_event_handler(event, project_name, file_path)

    def is_box_file(self, project_name, file_path):
        """
        Returns whether a file is a box.json that the discovery of a project
        whose components are found in the folders of its window can read:
        one under a folder of the window or an install path.
        """
        scope = self.scopes.get(project_name)
        if (
            not isinstance(scope, AutoScope)
            or os.path.basename(file_path) != 'box.json'
        ):
            return False
        project_data = self.data.get(project_name)
        install_paths = project_data['install_paths'] if project_data else []
        return any(
            project_files.is_under(folder, file_path)
            for folder in [*scope.folders, *install_paths]
        )

    def accepts_file(self, file_path):
        return component_parser.is_component_file(file_path)

    def index_folder(self, root_path):
        if self.parser is None:
            # it did not start, and the console has the reason
            return {}
        return self.parser.parse_directory(root_path)

    def index_file(self, file_path):
        if self.parser is None:
            return None
        return self.parser.parse_file(file_path)

    def build_project_data(
        self, project_name, index, previous, changed_files, sources=None
    ):
        mappings = self.get_project_data(project_name).get('mappings', [])

        cache = {}
        if previous:
            cache = {
                file_path: previews
                for file_path, previews in previous['cache'].items()
                if file_path not in changed_files
            }

        # a scan of the folders of the window gives their discoveries, which
        # an update keeps
        if sources is not None:
            automatic = True
            discoveries: dict[str, Discovery] = sources
        elif previous:
            automatic = previous['automatic']
            discoveries = previous['discoveries']
        else:
            automatic = False
            discoveries = {}
        install_paths = sorted(
            {
                install_path
                for discovery in discoveries.values()
                for install_path in discovery.install_paths
            }
        )

        # the chains only change with the files, and most updates are a save
        # of a file already in the index
        if (
            previous
            and previous['automatic'] == automatic
            and previous['index'].keys() == index.keys()
        ):
            suffixes = dot_paths.Suffixes(
                previous['file_suffixes'], previous['folder_suffixes']
            )
        else:
            if automatic:
                bases = dot_paths.get_bases(discoveries, install_paths)
            else:
                bases = dot_paths.get_configured_bases(
                    self.get_root_paths(project_name)
                )
            suffixes = dot_paths.build_suffixes(index, bases)

        project_data: ComponentProjectData = {
            'index': index,
            'file_paths': {file_path.lower(): file_path for file_path in index},
            'dot_paths': build_dot_paths(
                index, mappings, self.get_base_dir(project_name)
            ),
            'entities': build_entities(index),
            'cache': cache,
            'completions': {},
            'automatic': automatic,
            'discoveries': discoveries,
            'install_paths': install_paths,
            'file_suffixes': suffixes.files,
            'folder_suffixes': suffixes.folders,
        }

        # inheritance is resolved against these paths, not the published ones
        def get_extended_metadata(file_path):
            return self.extend_metadata(
                project_name, file_path, index[file_path], project_data
            )

        # a save of a file already in the index changes the completions of
        # that file and of those that extend it, as every extends resolves
        # to the same file when the files are the same
        if previous and changed_files and previous['index'].keys() == index.keys():
            extending = self.get_extending_files(
                project_name, project_data, changed_files
            )
            project_data['completions'] = {
                **previous['completions'],
                **completions.build(extending, get_extended_metadata),
            }
        else:
            project_data['completions'] = completions.build(
                index.keys(), get_extended_metadata
            )
        return project_data

    def get_extending_files(
        self, project_name, project_data: ComponentProjectData, file_paths
    ) -> list[str]:
        """
        Returns the files of the index that are among file_paths or extend
        one of them, directly or not.
        """
        index = project_data['index']
        extended_by: dict[str, list[str]] = {}
        for file_path, metadata in index.items():
            extends_file_path = self.resolve_path(
                project_name, file_path, metadata['extends'], project_data
            )
            if extends_file_path:
                extended_by.setdefault(extends_file_path, []).append(file_path)

        found = [file_path for file_path in file_paths if file_path in index]
        seen = set(found)
        for file_path in found:
            for child in extended_by.get(file_path, []):
                if child not in seen:
                    seen.add(child)
                    found.append(child)
        return found

    # each getter reads a project's data once, as a rebuild replaces it

    def get_project_index(self, project_name) -> dict[str, ComponentMetadata]:
        project_data = self.data.get(project_name)
        return project_data['index'] if project_data else {}

    def get_file_paths(self, project_name):
        return self.get_project_index(project_name).keys()

    def get_dot_paths(self, project_name) -> dict[str, DotPath]:
        project_data = self.data.get(project_name)
        return project_data['dot_paths'] if project_data else {}

    def get_entities(self, project_name) -> dict[str, Entity]:
        project_data = self.data.get(project_name)
        return project_data['entities'] if project_data else {}

    def get_file_path_by_dot_path(
        self, project_name, dot_path, from_file=None
    ) -> DotPath | None:
        """
        Returns the best of the indexed files that a dot path written in
        from_file resolves to, with the dot path the docs show for it.
        """
        resolution = self.resolve_dot_path(project_name, dot_path, from_file)
        if not resolution.file_paths:
            return None
        file_path = resolution.file_paths[0]
        return {
            'file_path': file_path,
            'dot_path': self.get_dot_path_name(
                project_name, file_path, dot_path, resolution
            ),
        }

    def get_dot_path_name(
        self, project_name, file_path, dot_path, resolution: dot_paths.Resolution
    ) -> str:
        """
        Returns the dot path that the docs show for a file a dot path
        resolved to: its dot path through a mapping when it has one, and
        otherwise the dot path written, cased as the file system has it.
        """
        if resolution.rule == 2:
            mapped = self.get_dot_paths(project_name).get(dot_path.lower())
            if mapped:
                return mapped['dot_path']
        return self.get_mapped_dot_path(
            project_name, file_path
        ) or dot_paths.cased_dot_path(file_path, dot_path)

    def get_mapped_dot_path(self, project_name, file_path) -> str | None:
        """Returns the dot path of a file through the first mapping it is under."""
        mappings = self.get_project_data(project_name).get('mappings', [])
        base_dir = self.get_base_dir(project_name)
        for mapping in mappings:
            path_parts = utils.get_mapped_path_parts(
                file_path, utils.normalize_mapping(mapping, base_dir)
            )
            if path_parts:
                return '.'.join(path_parts)[:-4]
        return None

    def get_file_path_by_entity_name(self, project_name, entity_name) -> Entity | None:
        return self.get_entities(project_name).get(entity_name.lower())

    def get_cache_by_file_path(self, project_name, file_path) -> dict[str, Any] | None:
        project_data = self.data.get(project_name)
        if not project_data or file_path not in project_data['index']:
            return None
        return project_data['cache'].setdefault(file_path, {})

    def get_metadata_by_file_path(
        self, project_name, file_path
    ) -> ComponentMetadata | None:
        return self.get_project_index(project_name).get(file_path)

    def get_extended_metadata_by_file_path(
        self, project_name, file_path
    ) -> ExtendedMetadata | None:
        """
        returns the full metadata for a given cfc file path
        this is used, rather than just `cfc_index[file_path]["functions"]`
        in order to take into account the `extends` attribute
        """
        project_data = self.data.get(project_name)
        if not project_data:
            return None
        metadata = project_data['index'].get(file_path)
        if not metadata:
            return None
        return self.extend_metadata(project_name, file_path, metadata, project_data)

    def extend_metadata(
        self,
        project_name,
        file_path,
        metadata: ComponentMetadata,
        project_data: ComponentProjectData | None = None,
        stack=None,
    ) -> ExtendedMetadata:
        """
        returns a copy of the metadata of the component at file_path with the
        functions and properties of the components it extends merged in, and
        maps each function and property to the file that declares it
        `extends` is resolved against project_data, which defaults to the
        project's published data
        """
        if project_data is None:
            project_data = self.data.get(project_name)
        if stack is None:
            stack = []

        extended_meta: ExtendedMetadata = {
            **metadata,
            'functions': {},
            'function_file_map': {},
            'properties': {},
            'property_file_map': {},
        }

        if project_data and metadata['extends'] and file_path not in stack:
            stack.append(file_path)
            extends_file_path = self.resolve_path(
                project_name, file_path, metadata['extends'], project_data
            )
            extends_meta = (
                project_data['index'].get(extends_file_path)
                if extends_file_path
                else None
            )
            if extends_meta:
                root_meta = self.extend_metadata(
                    project_name, extends_file_path, extends_meta, project_data, stack
                )
                extended_meta['functions'].update(root_meta['functions'])
                extended_meta['function_file_map'].update(
                    root_meta['function_file_map']
                )
                extended_meta['properties'].update(root_meta['properties'])
                extended_meta['property_file_map'].update(
                    root_meta['property_file_map']
                )

        extended_meta['functions'].update(metadata['functions'])
        extended_meta['function_file_map'].update(
            {funct_key: file_path for funct_key in metadata['functions']}
        )
        extended_meta['properties'].update(metadata['properties'])
        extended_meta['property_file_map'].update(
            {prop_key: file_path for prop_key in metadata['properties']}
        )
        return extended_meta

    def is_init_method(self, project_name, file_path, function_name) -> bool:
        """
        returns whether a lower case function name is that of the constructor
        of the component at file_path: its initmethod, or init, which a
        component that is not indexed is taken to have
        """
        metadata = self.get_metadata_by_file_path(project_name, file_path)
        init_method = (metadata['initmethod'] if metadata else None) or 'init'
        return function_name == init_method.lower()

    def get_metadata_by_dot_path(self, project_name, dot_path, from_file=None):
        cfc_file_path = self.get_file_path_by_dot_path(
            project_name, dot_path, from_file
        )
        if cfc_file_path:
            return self.get_metadata_by_file_path(
                project_name, cfc_file_path['file_path']
            )
        return None

    def get_completions_by_file_path(
        self, project_name, file_path
    ) -> completions.TypeCompletions | None:
        comp_type = utils.get_setting('cfml_cfc_completions')
        project_data = self.data.get(project_name)
        if not project_data or file_path not in project_data['completions']:
            return None
        return project_data['completions'][file_path].get(comp_type)

    def get_completions_by_dot_path(self, project_name, dot_path, from_file=None):
        cfc_file_path = self.get_file_path_by_dot_path(
            project_name, dot_path, from_file
        )
        if cfc_file_path:
            return self.get_completions_by_file_path(
                project_name, cfc_file_path['file_path']
            )
        return None

    def get_completions_by_entity_name(self, project_name, entity_name):
        cfc_file_path = self.get_file_path_by_entity_name(project_name, entity_name)
        if cfc_file_path:
            return self.get_completions_by_file_path(
                project_name, cfc_file_path['file_path']
            )
        return None

    def resolve_dot_path(
        self,
        project_name,
        dot_path,
        from_file=None,
        project_data: ComponentProjectData | None = None,
        exclude=None,
    ) -> dot_paths.Resolution:
        """
        Returns the indexed files that a dot path written in from_file
        resolves to, best first, by the rules in dot_paths.py, leaving out
        the excluded file. It is resolved against project_data, which
        defaults to the project's published data.
        """
        if project_data is None:
            project_data = self.data.get(project_name)
        if not project_data:
            return dot_paths.NOT_FOUND
        return dot_paths.resolve(project_data, dot_path, from_file, exclude)

    def resolve_path(
        self,
        project_name,
        file_path,
        extends,
        project_data: ComponentProjectData | None = None,
    ) -> str | None:
        """
        Returns the file of the component that the one at file_path
        extends, the best of those the dot path resolves to; a component
        does not extend itself. A buffer that has not been saved has no
        file_path, and extends is None for a component that extends nothing.
        """
        resolution = self.resolve_dot_path(
            project_name, extends, file_path, project_data, exclude=file_path
        )
        return resolution.file_paths[0] if resolution.file_paths else None

    def get_folder_mapping(self, project_name, file_path):
        mappings = self.get_project_data(project_name).get('mappings', [])
        base_dir = self.get_base_dir(project_name)
        normalized_file_path = utils.normalize_path(file_path)
        for mapping in mappings:
            normalized_mapping = utils.normalize_mapping(mapping, base_dir)
            path_parts = utils.get_mapped_path_parts(
                normalized_file_path, normalized_mapping
            )
            if not path_parts:
                continue
            dot_path = '.'.join(path_parts[:-1])
            if len(dot_path) > 0:
                return dot_path
        return None
