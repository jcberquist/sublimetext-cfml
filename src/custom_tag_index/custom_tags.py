import sublime
from typing import Any, TypedDict
from ..project_index import ProjectIndex
from .. import kinds
from .. import utils
from .custom_tag_index import (
    index as index_tag_folder,
    index_file as index_tag_file,
    is_custom_tag_file,
)


def generate_tag_map(custom_tag_folders, index, base_dir):
    tag_map = {}
    for tag_folder in custom_tag_folders:
        root_path = utils.normalize_path(tag_folder['path'], base_dir)
        for file_path in index:
            if file_path.startswith(root_path + '/'):
                prefix = tag_folder['prefix'] + ':' if 'prefix' in tag_folder else 'cf_'
                tag_map[prefix + index[file_path]['tag_name']] = file_path
    return tag_map


def generate_completions_and_closing_tags(custom_tag_folders, index, base_dir):
    prefixes = []
    tags = {}
    attributes = {}
    closing_tags = []

    for tag_folder in custom_tag_folders:
        root_path = utils.normalize_path(tag_folder['path'], base_dir)
        if 'prefix' in tag_folder:
            prefixes.append(
                sublime.CompletionItem(
                    tag_folder['prefix'],
                    'custom tag prefix (cfml)',
                    tag_folder['prefix'] + ':',
                    kind=kinds.CUSTOM_TAG_PREFIX,
                )
            )
        for file_path in index:
            if file_path.startswith(root_path + '/'):
                prefix = tag_folder['prefix'] if 'prefix' in tag_folder else 'cf_'
                if prefix not in tags:
                    tags[prefix] = []
                key = (
                    prefix
                    + (':' if 'prefix' in tag_folder else '')
                    + index[file_path]['tag_name']
                )
                tags[prefix].append(
                    make_tag_completion(prefix, index[file_path]['tag_name'])
                )
                attributes[key] = [
                    sublime.CompletionItem(
                        a,
                        key,
                        a + '="$1"',
                        sublime.CompletionFormat.SNIPPET,
                        kind=kinds.ATTRIBUTE,
                    )
                    for a in index[file_path]['attributes']
                ]
                if index[file_path]['has_end_tag']:
                    closing_tags.append(key)

    return {'prefixes': prefixes, 'tags': tags, 'attributes': attributes}, closing_tags


def make_tag_completion(prefix, tag):
    suffix = ' (' + prefix + ')' if prefix != 'cf_' else ''
    comp_prefix = 'cf_' if prefix == 'cf_' else ''
    return sublime.CompletionItem(
        comp_prefix + tag,
        'custom tag' + suffix,
        kind=kinds.CUSTOM_TAG,
    )


class CustomTagProjectData(TypedDict):
    """The custom tags of a project and what is derived from them."""

    # what was found in each custom tag file, by path
    index: dict[str, dict[str, Any]]
    # the file of each tag, by its name with its prefix
    tags: dict[str, str]
    # the "prefixes", "tags" and "attributes" completions
    completions: dict[str, Any]
    # the names of the tags that have an end tag
    closing_tags: list[str]


class CustomTags(ProjectIndex[CustomTagProjectData]):
    label = 'custom tags'

    def __init__(self):
        super().__init__('custom_tag_folders')

    def accepts_file(self, file_path):
        return is_custom_tag_file(file_path)

    def index_folder(self, root_path):
        return index_tag_folder(root_path)

    def index_file(self, file_path):
        return index_tag_file(file_path)

    def build_project_data(
        self, project_name, index, previous, changed_files, sources=None
    ):
        custom_tag_folders = self.get_folders(project_name)
        base_dir = self.get_base_dir(project_name)

        tags = generate_tag_map(custom_tag_folders, index, base_dir)
        completions, closing_tags = generate_completions_and_closing_tags(
            custom_tag_folders, index, base_dir
        )

        return {
            'index': index,
            'tags': tags,
            'completions': completions,
            'closing_tags': closing_tags,
        }

    # each getter reads a project's data once, as a rebuild replaces it

    def get_prefix_completions(self, project_name):
        completions = []
        project_data = self.data.get(project_name)
        if project_data:
            completions.extend(project_data['completions']['prefixes'])
            if 'cf_' in project_data['completions']['tags']:
                completions.extend(project_data['completions']['tags']['cf_'])
            if len(completions) > 0:
                return completions
        return None

    def get_tag_completions(self, project_name, prefix):
        project_data = self.data.get(project_name)
        if project_data:
            if prefix in project_data['completions']['tags']:
                return project_data['completions']['tags'][prefix]
        return None

    def get_tag_attribute_completions(self, project_name, tag_name):
        project_data = self.data.get(project_name)
        if project_data:
            if tag_name in project_data['completions']['attributes']:
                return project_data['completions']['attributes'][tag_name]
        return None

    def get_index_by_tag_name(self, project_name, tag_name):
        project_data = self.data.get(project_name)
        if project_data:
            if tag_name in project_data['tags']:
                file_path = project_data['tags'][tag_name]
                return file_path, project_data['index'][file_path]
        return None, None

    def get_closing_custom_tags(self, project_name):
        project_data = self.data.get(project_name)
        if project_data:
            return project_data['closing_tags']
        return []
