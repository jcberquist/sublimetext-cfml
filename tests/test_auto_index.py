import json
from dataclasses import replace

import pytest
from index_helpers import add_project, git_repo, write

from CFML.src.component_index.index import AutoScope
from CFML.src.project_files import Discovery
from CFML.src.project_watcher import Project, project_watcher

BASE = 'component { function inherited() {} }'
CHILD = 'component extends="Base" { function own() {} }'
ENTITY = 'component persistent="true" entityname="Account" {}'


@pytest.fixture(autouse=True)
def uses_git(git_environment):
    pass


def make_site(tmp_path):
    """
    A git folder with a model, an ignored folder, and a box.json that installs
    into the ignored lib folder.
    """
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\ntmp/\n')
    write(site / 'box.json', json.dumps({'installPaths': {'coldbox': 'lib/coldbox'}}))
    write(site / 'model' / 'Base.cfc', BASE)
    write(site / 'model' / 'Child.cfc', CHILD)
    write(site / 'model' / 'Account.cfc', ENTITY)
    write(site / 'tmp' / 'Cached.cfc')
    write(site / 'lib' / 'coldbox' / 'system' / 'Controller.cfc')
    return site


def completion_names(index, project_name, file_path):
    completions = index.get_completions_by_file_path(project_name, file_path)
    return [completion.name for completion in completions['functions']]


def indexed(index, project_name, root):
    # the indexed paths, relative to root
    root = root.as_posix() + '/'
    return sorted(path.replace(root, '') for path in index.get_file_paths(project_name))


def test_a_folder_without_a_project_file_is_indexed(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])

    assert indexed(index, project_name, site) == [
        'lib/coldbox/system/Controller.cfc',
        'model/Account.cfc',
        'model/Base.cfc',
        'model/Child.cfc',
    ]
    project_data = index.data[project_name]
    assert project_data['automatic'] is True
    assert project_data['install_paths'] == [(site / 'lib' / 'coldbox').as_posix()]
    assert list(project_data['discoveries']) == [site.as_posix()]
    assert project_data['discoveries'][site.as_posix()].source == 'git'
    # there are no mappings to give dot paths
    assert project_data['dot_paths'] == {}


def test_entities_and_relative_extends_work_without_a_project_file(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])

    child = (site / 'model' / 'Child.cfc').as_posix()
    assert completion_names(index, project_name, child) == ['inherited', 'own']
    assert index.get_file_path_by_entity_name(project_name, 'account') == {
        'file_path': (site / 'model' / 'Account.cfc').as_posix(),
        'entity_name': 'Account',
    }


def test_the_console_names_the_folders_and_the_source(tmp_path, index, capsys):
    site = make_site(tmp_path)
    add_project([site])

    out = capsys.readouterr().out
    assert f"CFML: indexing components in folder '{site.as_posix()}'" in out
    assert (
        f"CFML: found 4 component files in '{site.as_posix()}'"
        ' (git, 1 of them in 1 install path)'
    ) in out
    assert f"in folder '{site.as_posix()}' completed - 4 files indexed" in out


def test_a_folder_that_is_not_a_git_work_tree(tmp_path, index, capsys):
    marked = tmp_path / 'marked'
    write(marked / 'Application.cfc')
    write(marked / 'model' / 'User.cfc')
    plain = tmp_path / 'plain'
    write(plain / 'model' / 'User.cfc')
    project_name = add_project([marked, plain])

    assert indexed(index, project_name, tmp_path) == [
        'marked/Application.cfc',
        'marked/model/User.cfc',
    ]
    out = capsys.readouterr().out
    assert f"found 2 component files in '{marked.as_posix()}' (walk)" in out
    # a folder with nothing of CFML is not worth a line
    assert f"indexing '{plain.as_posix()}'" not in out


def test_a_folder_over_the_cap_is_not_indexed(tmp_path, index, settings, capsys):
    site = make_site(tmp_path)
    settings['cfml_index_max_files'] = 3
    project_name = add_project([site])

    assert index.get_project_index(project_name) == {}
    # the console says why, and nothing about indexing no files
    assert capsys.readouterr().out == (
        f"CFML: not indexing '{site.as_posix()}' (git) - more than 3 component files\n"
    )

    # and a file saved there is not indexed either
    new = write(site / 'model' / 'New.cfc')
    project_watcher.notify('project_file_updated', project_name, new)
    assert index.get_project_index(project_name) == {}


def test_a_window_without_cfml_says_nothing(tmp_path, index, capsys):
    # a git folder with no component files, and a folder that is not a git
    # work tree and has no marker
    empty = git_repo(tmp_path / 'empty')
    write(empty / 'README.md', 'nothing here')
    plain = tmp_path / 'plain'
    write(plain / 'model' / 'User.cfc')
    project_name = add_project([empty, plain])

    assert index.get_project_index(project_name) == {}
    assert capsys.readouterr().out == ''

    # nor when the project is updated
    project_watcher.notify('project_updated', project_name)
    assert capsys.readouterr().out == ''


def test_a_folder_without_cfml_is_left_out_of_the_console(tmp_path, index, capsys):
    site = make_site(tmp_path)
    empty = git_repo(tmp_path / 'empty')
    add_project([site, empty])

    out = capsys.readouterr().out
    assert f"found 4 component files in '{site.as_posix()}'" in out
    assert f"in '{empty.as_posix()}'" not in out
    assert f"indexing '{empty.as_posix()}'" not in out
    assert 'completed - 4 files indexed' in out


def test_a_project_with_empty_cfc_folders_still_says_so(tmp_path, index, capsys):
    site = make_site(tmp_path)
    (site / 'empty').mkdir()
    project_file = site / 'site.sublime-project'
    add_project([site], {'cfc_folders': [{'path': 'empty'}]}, project_file)

    out = capsys.readouterr().out
    assert f"CFML: indexing components in project '{project_file.as_posix()}'" in out
    assert 'completed - 0 files indexed' in out


def test_the_cap_is_per_project(tmp_path, index, settings):
    site = make_site(tmp_path)
    settings['cfml_index_max_files'] = 3
    project_file = tmp_path / 'site.sublime-project'
    project_name = add_project([site], {'cfml_index_max_files': 10}, project_file)

    assert len(index.get_project_index(project_name)) == 4


def test_a_new_file_is_indexed_on_save(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])

    new = write(site / 'model' / 'New.cfc')
    project_watcher.notify('project_file_updated', project_name, new)
    assert new in index.get_project_index(project_name)


def test_an_ignored_file_is_not_indexed_on_save(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])
    published = index.data[project_name]

    ignored = write(site / 'tmp' / 'Other.cfc')
    project_watcher.notify('project_file_updated', project_name, ignored)
    assert index.data[project_name] is published


def test_a_file_under_an_install_path_is_indexed_on_save(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])

    installed = write(site / 'lib' / 'coldbox' / 'system' / 'Injector.cfc')
    project_watcher.notify('project_file_updated', project_name, installed)
    assert installed in index.get_project_index(project_name)


def test_a_changed_file_is_indexed_on_save(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])
    child = (site / 'model' / 'Child.cfc').as_posix()

    write(site / 'model' / 'Child.cfc', CHILD.replace('own', 'renamed'))
    project_watcher.notify('project_file_updated', project_name, child)
    assert completion_names(index, project_name, child) == ['inherited', 'renamed']
    # an update keeps how the files were found
    assert index.data[project_name]['automatic'] is True
    assert list(index.data[project_name]['discoveries']) == [site.as_posix()]


def test_only_components_are_indexed_on_save(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])
    published = index.data[project_name]

    page = write(site / 'model' / 'page.cfm', '<p>')
    project_watcher.notify('project_file_updated', project_name, page)
    assert index.data[project_name] is published


def test_a_deleted_file_is_removed(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])
    base = site / 'model' / 'Base.cfc'

    base.unlink()
    project_watcher.notify('project_file_removed', project_name, base.as_posix())
    assert base.as_posix() not in index.get_project_index(project_name)
    child = (site / 'model' / 'Child.cfc').as_posix()
    assert completion_names(index, project_name, child) == ['own']


def test_two_folders_in_one_window(tmp_path, index):
    site = make_site(tmp_path)
    other = git_repo(tmp_path / 'other')
    write(other / 'Other.cfc')
    project_name = add_project([site, other])

    files = index.get_project_index(project_name)
    assert (other / 'Other.cfc').as_posix() in files
    assert (site / 'model' / 'Base.cfc').as_posix() in files
    assert list(index.data[project_name]['discoveries']) == [
        other.as_posix(),
        site.as_posix(),
    ]

    # a save is checked against the folder it is in
    new = write(other / 'New.cfc')
    project_watcher.notify('project_file_updated', project_name, new)
    assert new in index.get_project_index(project_name)


def test_a_folder_inside_another_one_of_the_window(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site, site / 'model'])

    assert len(index.get_project_index(project_name)) == 4


def test_nothing_is_indexed_when_the_setting_is_off(tmp_path, index, settings):
    site = make_site(tmp_path)
    settings['cfml_auto_index'] = False
    project_name = add_project([site])

    assert project_name not in index.data
    assert index.get_scope(project_name) is None


def test_a_project_can_turn_the_setting_on_or_off(tmp_path, index, settings):
    site = make_site(tmp_path)
    project_file = tmp_path / 'site.sublime-project'
    settings['cfml_auto_index'] = False
    project_name = add_project([site], {'cfml_auto_index': True}, project_file)
    assert len(index.get_project_index(project_name)) == 4

    project = project_watcher.projects[project_name]
    project_watcher.project_updated(replace(project, data={}))
    assert project_name not in index.data


def test_an_empty_cfc_folders_indexes_nothing(tmp_path, index):
    site = make_site(tmp_path)
    project_file = tmp_path / 'site.sublime-project'
    project_name = add_project([site], {'cfc_folders': []}, project_file)

    assert project_name not in index.data


def test_cfc_folders_index_only_those_folders(tmp_path, index):
    site = make_site(tmp_path)
    project_file = site / 'site.sublime-project'
    data = {'cfc_folders': [{'path': 'tmp'}]}
    project_name = add_project([site], data, project_file)

    assert indexed(index, project_name, site) == ['tmp/Cached.cfc']
    project_data = index.data[project_name]
    assert project_data['automatic'] is False
    assert project_data['discoveries'] == {}
    assert project_data['install_paths'] == []

    # and only what is in them is indexed on save
    new = write(site / 'model' / 'New.cfc')
    project_watcher.notify('project_file_updated', project_name, new)
    assert indexed(index, project_name, site) == ['tmp/Cached.cfc']


def test_adding_cfc_folders_to_the_project_file_switches_mode(tmp_path, index):
    site = make_site(tmp_path)
    project_file = site / 'site.sublime-project'
    project_name = add_project([site], {}, project_file)
    assert len(index.get_project_index(project_name)) == 4

    project = project_watcher.projects[project_name]
    data = {'cfc_folders': [{'path': 'tmp'}]}
    project_watcher.project_updated(replace(project, data=data))
    assert indexed(index, project_name, site) == ['tmp/Cached.cfc']
    assert index.data[project_name]['automatic'] is False

    project = project_watcher.projects[project_name]
    project_watcher.project_updated(replace(project, data={}))
    assert len(index.get_project_index(project_name)) == 4
    assert index.data[project_name]['automatic'] is True


def test_a_project_file_window_is_reindexed_when_its_folders_change(
    tmp_path, index, open_window
):
    site = make_site(tmp_path)
    other = git_repo(tmp_path / 'other')
    other_file = write(other / 'Other.cfc')
    project_file = (tmp_path / 'site.sublime-project').as_posix()
    window = open_window([site.as_posix()], project_file, {})
    project_watcher.sync_projects()
    assert len(index.get_project_index(project_file)) == 4

    window.folder_list.append(other.as_posix())
    project_watcher.check_window(window)
    assert index.scopes[project_file] == AutoScope(
        (other.as_posix(), site.as_posix()), 5000
    )
    assert other_file in index.get_project_index(project_file)

    window.folder_list.remove(site.as_posix())
    project_watcher.check_window(window)
    assert list(index.get_project_index(project_file)) == [other_file]


def test_a_folders_window_follows_its_folders(tmp_path, index, open_window, windows):
    site = make_site(tmp_path)
    other = git_repo(tmp_path / 'other')
    other_file = write(other / 'Other.cfc')
    window = open_window([site.as_posix()])
    project_watcher.sync_projects()
    first = 'folders:' + site.as_posix()
    assert len(index.get_project_index(first)) == 4

    window.folder_list.append(other.as_posix())
    project_watcher.check_window(window)
    second = 'folders:' + '|'.join(sorted([site.as_posix(), other.as_posix()]))
    assert first not in index.data
    assert other_file in index.get_project_index(second)

    windows.clear()
    project_watcher.sync_projects()
    assert index.data == {}


def test_a_saved_file_of_a_project_being_indexed_waits_for_the_index(tmp_path, index):
    # until a project's index is published there is nothing to check a save
    # against; the index that is published lists the file
    site = make_site(tmp_path)
    name = 'folders:' + site.as_posix()
    project_watcher.projects[name] = Project(name, {}, None, (site.as_posix(),))
    index.scopes[name] = index.get_scope(name)

    new = write(site / 'model' / 'New.cfc')
    project_watcher.notify('project_file_updated', name, new)
    assert name not in index.data
    index.index_project(name)
    assert new in index.get_project_index(name)


def test_discoveries_are_kept_per_folder(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])
    discovery = index.data[project_name]['discoveries'][site.as_posix()]

    assert isinstance(discovery, Discovery)
    assert discovery.install_paths == index.data[project_name]['install_paths']


def test_a_saved_box_json_indexes_the_project_again(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])
    module = write(site / 'modules' / 'cbauth' / 'models' / 'Auth.cfc')
    write(site / '.gitignore', 'lib/\ntmp/\nmodules/\n')
    assert module not in index.get_project_index(project_name)

    box = write(
        site / 'box.json',
        json.dumps(
            {'installPaths': {'coldbox': 'lib/coldbox', 'cbauth': 'modules/cbauth'}}
        ),
    )
    project_watcher.notify('project_file_updated', project_name, box)
    assert module in index.get_project_index(project_name)
    assert index.data[project_name]['install_paths'] == [
        (site / 'lib' / 'coldbox').as_posix(),
        (site / 'modules' / 'cbauth').as_posix(),
    ]


def test_a_deleted_box_json_indexes_the_project_again(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])
    box = site / 'box.json'

    box.unlink()
    project_watcher.notify('project_file_removed', project_name, box.as_posix())
    assert indexed(index, project_name, site) == [
        'model/Account.cfc',
        'model/Base.cfc',
        'model/Child.cfc',
    ]
    assert index.data[project_name]['install_paths'] == []


def test_a_box_json_saved_in_a_folder_without_a_marker(tmp_path, index):
    plain = tmp_path / 'plain'
    user = write(plain / 'model' / 'User.cfc')
    project_name = add_project([plain])
    assert index.get_project_index(project_name) == {}

    box = write(plain / 'box.json', '{}')
    project_watcher.notify('project_file_updated', project_name, box)
    assert list(index.get_project_index(project_name)) == [user]


def test_other_box_json_files_do_not_index_the_project_again(
    tmp_path, index, monkeypatch
):
    site = make_site(tmp_path)
    elsewhere = write(tmp_path / 'elsewhere' / 'box.json', '{}')
    project_name = add_project([site])
    configured_name = add_project(
        [site], {'cfc_folders': [{'path': 'model'}]}, site / 'site.sublime-project'
    )
    reindexed = []
    monkeypatch.setattr(index, 'reindex_project', reindexed.append)

    project_watcher.notify('project_file_updated', project_name, elsewhere)
    box = (site / 'box.json').as_posix()
    project_watcher.notify('project_file_updated', configured_name, box)
    assert reindexed == []


def test_the_folder_chains_of_the_files_are_indexed(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])

    project_data = index.data[project_name]
    controller = (site / 'lib' / 'coldbox' / 'system' / 'Controller.cfc').as_posix()
    assert project_data['file_suffixes']['coldbox.system.controller'] == [controller]
    assert project_data['file_suffixes']['lib.coldbox.system.controller'] == [
        controller
    ]
    assert project_data['folder_suffixes']['model'] == [(site / 'model').as_posix()]


def test_a_save_keeps_the_folder_chains_unless_the_files_change(tmp_path, index):
    site = make_site(tmp_path)
    project_name = add_project([site])
    suffixes = index.data[project_name]['file_suffixes']

    child = (site / 'model' / 'Child.cfc').as_posix()
    write(site / 'model' / 'Child.cfc', CHILD.replace('own', 'renamed'))
    project_watcher.notify('project_file_updated', project_name, child)
    assert index.data[project_name]['file_suffixes'] is suffixes

    new = write(site / 'model' / 'New.cfc')
    project_watcher.notify('project_file_updated', project_name, new)
    assert index.data[project_name]['file_suffixes']['model.new'] == [new]
    assert 'model.new' not in suffixes


def test_the_folder_chains_of_cfc_folders_start_with_their_name(tmp_path, index):
    site = make_site(tmp_path)
    project_file = site / 'site.sublime-project'
    data = {'cfc_folders': [{'path': 'model'}]}
    project_name = add_project([site], data, project_file)

    base = (site / 'model' / 'Base.cfc').as_posix()
    assert index.data[project_name]['file_suffixes']['model.base'] == [base]
    assert 'site.model.base' not in index.data[project_name]['file_suffixes']
