import pytest

from CFML.src.project_index import ProjectIndex, Scan
from CFML.src.project_watcher import Project, project_watcher


class TextIndex(ProjectIndex):
    """Indexes the .txt files of the folders a project lists under text."""

    label = 'texts'

    def __init__(self):
        super().__init__('text_folders')
        self.scanned = []

    def accepts_file(self, file_path):
        return file_path.endswith('.txt')

    def index_folder(self, root_path):
        self.scanned.append(root_path)
        return {}

    def index_file(self, file_path):
        return {'text': True}

    def build_project_data(
        self, project_name, index, previous, changed_files, sources=None
    ):
        return {'index': index, 'sources': sources}


@pytest.fixture
def text_index():
    index = TextIndex()
    yield index
    index.close()


def test_the_default_scope_is_the_root_paths_in_the_order_of_their_paths(
    tmp_path, project, text_index
):
    base_dir = tmp_path.as_posix()
    project_name = project({'text_folders': [{'path': 'b'}, {'path': 'a'}]})

    assert text_index.get_scope(project_name) == (base_dir + '/a', base_dir + '/b')
    text_index.reindex_project(project_name)
    assert text_index.scanned == [base_dir + '/a', base_dir + '/b']
    assert text_index.data[project_name] == {'index': {}, 'sources': None}


def test_a_project_without_folders_has_no_scope(project, text_index):
    project_name = project({})

    assert text_index.get_scope(project_name) is None
    text_index.reindex_project(project_name)
    assert project_name not in text_index.data


def test_an_update_reindexes_only_when_the_scope_changed(tmp_path, project, text_index):
    project_name = project({'text_folders': [{'path': 'a'}]})
    text_index.reindex_project(project_name)
    text_index.scanned.clear()

    text_index.project_event_handler('project_updated', project_name)
    assert text_index.scanned == []

    project_watcher.get_project_data(project_name)['text_folders'].append({'path': 'b'})
    text_index.project_event_handler('project_updated', project_name)
    assert len(text_index.scanned) == 2


def test_the_sources_of_a_scan_are_given_to_a_build_from_scratch(
    project, text_index, monkeypatch
):
    project_name = project({'text_folders': [{'path': 'a'}]})
    monkeypatch.setattr(
        text_index, 'scan', lambda project_name, scope: Scan({}, 'found')
    )
    text_index.reindex_project(project_name)
    assert text_index.data[project_name]['sources'] == 'found'

    # an update keeps what it has
    text_index.update_project_file(project_name, '/elsewhere/new.txt')
    assert text_index.data[project_name]['sources'] is None


def test_only_files_in_the_index_are_removed(tmp_path, project, text_index):
    project_name = project({'text_folders': [{'path': 'a'}]})
    text_index.reindex_project(project_name)
    published = text_index.data[project_name]

    text_index.project_event_handler(
        'project_file_removed', project_name, tmp_path.as_posix() + '/a/no.txt'
    )
    assert text_index.data[project_name] is published


def test_a_project_is_described_by_its_file_or_its_folders(
    project, text_index, monkeypatch
):
    project_name = project({})
    assert text_index.describe_project(project_name) == f"project '{project_name}'"

    for name, folders in [
        ('folders:/a', ('/a',)),
        ('folders:/a|/b', ('/a', '/b')),
    ]:
        monkeypatch.setitem(
            project_watcher.projects, name, Project(name, {}, None, folders)
        )
    assert text_index.describe_project('folders:/a') == "folder '/a'"
    assert text_index.describe_project('folders:/a|/b') == "folders '/a', '/b'"
