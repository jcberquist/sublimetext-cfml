import json
import os
import subprocess

import pytest

from CFML.src import project_files
from CFML.src.project_files import Discovery, covers, discover

COMPONENT = 'component {}'


@pytest.fixture(autouse=True)
def git_environment(tmp_path, monkeypatch):
    # git reads no configuration but the repository's own, and finds no
    # repository above tmp_path
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', os.devnull)
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'xdg'))
    monkeypatch.setenv('GIT_CEILING_DIRECTORIES', str(tmp_path))


def write(path, text=COMPONENT):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path.as_posix()


def git(folder, *args):
    subprocess.run(
        [
            'git',
            '-c',
            'user.name=Test',
            '-c',
            'user.email=test@example.com',
            '-c',
            'init.defaultBranch=main',
            '-C',
            str(folder),
            *args,
        ],
        check=True,
        capture_output=True,
    )


def git_repo(folder):
    folder.mkdir(parents=True, exist_ok=True)
    git(folder, 'init', '-q')
    return folder


def commit_all(folder):
    git(folder, 'add', '-A')
    git(folder, 'commit', '-q', '-m', 'files')


def test_git_folder_lists_tracked_and_untracked_files(tmp_path):
    site = git_repo(tmp_path / 'site')
    tracked = write(site / 'model' / 'User.cfc')
    commit_all(site)
    untracked = write(site / 'model' / 'Order.cfc')
    write(site / 'views' / 'index.cfm', '<p>')

    discovery = discover(str(site), 100)

    assert discovery == Discovery(sorted([tracked, untracked]), [], 'git', None)


def test_git_folder_leaves_out_ignored_files(tmp_path):
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'tmp/\n*.bak.cfc\n')
    kept = write(site / 'model' / 'User.cfc')
    write(site / 'model' / 'User.bak.cfc')
    write(site / 'tmp' / 'Cached.cfc')

    assert discover(str(site), 100).files == [kept]


def test_git_folder_drops_tracked_files_deleted_from_disk(tmp_path):
    site = git_repo(tmp_path / 'site')
    kept = write(site / 'Kept.cfc')
    deleted = site / 'Deleted.cfc'
    write(deleted)
    commit_all(site)
    deleted.unlink()

    assert discover(str(site), 100).files == [kept]


def test_git_folder_lists_only_files_with_the_cfc_suffix(tmp_path):
    site = git_repo(tmp_path / 'site')
    kept = write(site / 'User.cfc')
    write(site / 'Upper.CFC')
    write(site / 'notes.cfc.txt', 'text')

    assert discover(str(site), 100).files == [kept]


def test_git_folder_handles_spaces_and_non_ascii_names(tmp_path):
    site = git_repo(tmp_path / 'my site é')
    tracked = write(site / 'modèles' / 'Ünïcode Service.cfc')
    commit_all(site)
    untracked = write(site / 'modèles' / 'Çache Service.cfc')

    discovery = discover(str(site), 100)

    assert discovery.files == sorted([tracked, untracked])
    assert all(os.path.isfile(path) for path in discovery.files)


def test_folder_inside_a_git_work_tree(tmp_path):
    repo = git_repo(tmp_path / 'repo')
    inside = write(repo / 'site' / 'model' / 'User.cfc')
    write(repo / 'other' / 'Other.cfc')

    discovery = discover(str(repo / 'site'), 100)

    assert discovery == Discovery([inside], [], 'git', None)


def test_paths_are_normalized(tmp_path):
    site = git_repo(tmp_path / 'site')
    path = write(site / 'User.cfc')

    discovery = discover(str(site) + os.sep, 100)

    assert discovery.files == [path]
    assert not any('\\' in path or '//' in path for path in discovery.files)


def test_install_paths_of_a_root_and_a_nested_box_json(tmp_path):
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\nmodules/app/modules/\n')
    write(
        site / 'box.json',
        json.dumps({'installPaths': {'coldbox': 'lib/coldbox/', 'gone': 'lib/gone'}}),
    )
    write(
        site / 'modules' / 'app' / 'box.json',
        json.dumps({'installPaths': {'cborm': 'modules/cborm/'}}),
    )
    own = write(site / 'modules' / 'app' / 'models' / 'Post.cfc')
    framework = write(site / 'lib' / 'coldbox' / 'system' / 'Controller.cfc')
    orm = write(site / 'modules' / 'app' / 'modules' / 'cborm' / 'Base.cfc')
    write(site / 'lib' / 'other' / 'Other.cfc')
    write(site / 'lib' / 'coldbox' / 'node_modules' / 'x' / 'X.cfc')
    write(site / 'lib' / 'coldbox' / '.engine' / 'Engine.cfc')
    # the box.json of an installed package is not read
    write(
        site / 'lib' / 'coldbox' / 'box.json',
        json.dumps({'installPaths': {'other': '../other/'}}),
    )

    discovery = discover(str(site), 100)

    assert discovery == Discovery(
        sorted([own, framework, orm]),
        [
            (site / 'lib' / 'coldbox').as_posix(),
            (site / 'modules' / 'app' / 'modules' / 'cborm').as_posix(),
        ],
        'git',
        None,
    )


def test_install_path_tracked_by_git_gives_no_duplicates(tmp_path):
    site = git_repo(tmp_path / 'site')
    write(site / 'box.json', json.dumps({'installPaths': {'dep': 'deps/dep'}}))
    tracked = write(site / 'deps' / 'dep' / 'Dep.cfc')

    discovery = discover(str(site), 100)

    assert discovery.files == [tracked]
    assert discovery.install_paths == [(site / 'deps' / 'dep').as_posix()]


def test_install_path_inside_another_is_walked_once(tmp_path):
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\n')
    write(
        site / 'box.json',
        json.dumps({'installPaths': {'a': 'lib/a', 'b': 'lib/a/modules/b'}}),
    )
    a = write(site / 'lib' / 'a' / 'A.cfc')
    b = write(site / 'lib' / 'a' / 'modules' / 'b' / 'B.cfc')

    discovery = discover(str(site), 100)

    assert discovery.files == sorted([a, b])
    assert discovery.install_paths == [(site / 'lib' / 'a').as_posix()]


@pytest.mark.parametrize(
    'text',
    [
        '{"installPaths": {"dep": ',
        '["lib/dep"]',
        '{"installPaths": ["lib/dep"]}',
        '{"installPaths": {"dep": 1, "none": null, "empty": ""}}',
    ],
)
def test_box_json_that_cannot_be_used_is_skipped(tmp_path, text):
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\n')
    write(site / 'box.json', text)
    write(site / 'lib' / 'dep' / 'Dep.cfc')
    own = write(site / 'Own.cfc')

    assert discover(str(site), 100) == Discovery([own], [], 'git', None)


def test_cap_counts_own_and_dependency_files(tmp_path):
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\n')
    write(site / 'box.json', json.dumps({'installPaths': {'dep': 'lib/dep'}}))
    for name in 'ABC':
        write(site / f'{name}.cfc')
        write(site / 'lib' / 'dep' / f'{name}.cfc')

    assert len(discover(str(site), 6).files) == 6
    assert discover(str(site), 5) == Discovery(
        [], [], 'git', 'more than 5 component files'
    )
    assert discover(str(site), 2) == Discovery(
        [], [], 'git', 'more than 2 component files'
    )


def test_walk_of_install_paths_stops_after_too_many_entries(tmp_path, monkeypatch):
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\n')
    write(site / 'box.json', json.dumps({'installPaths': {'dep': 'lib/dep'}}))
    for index in range(20):
        write(site / 'lib' / 'dep' / f'page{index}.cfm', '<p>')
    monkeypatch.setattr(project_files, 'MAX_WALK_ENTRIES', 10)

    assert discover(str(site), 100) == Discovery(
        [], [], 'git', 'more than 10 files and folders to look at'
    )


def test_folder_without_git_and_without_marker_is_not_listed(tmp_path):
    folder = tmp_path / 'folder'
    write(folder / 'model' / 'User.cfc')

    discovery = discover(str(folder), 100)

    assert discovery.files == []
    assert discovery.source == 'none'
    assert discovery.reason


@pytest.mark.parametrize(
    'marker',
    [
        'box.json',
        'server.json',
        'server-lucee.json',
        'Application.cfc',
        'Application.cfm',
        '.cfconfig.json',
    ],
)
def test_folder_without_git_with_a_marker_is_walked(tmp_path, marker):
    folder = tmp_path / 'folder'
    write(folder / marker, '{}')
    user = write(folder / 'model' / 'User.cfc')
    write(folder / 'node_modules' / 'x' / 'X.cfc')
    write(folder / '.hidden' / 'Hidden.cfc')
    expected = sorted([user, (folder / marker).as_posix()])
    if marker != 'Application.cfc':
        expected.remove((folder / marker).as_posix())

    assert discover(str(folder), 100) == Discovery(expected, [], 'walk', None)


def test_walked_folder_reads_its_box_json_files(tmp_path):
    folder = tmp_path / 'folder'
    write(
        folder / 'box.json',
        json.dumps({'installPaths': {'in': 'lib/in', 'out': '../shared'}}),
    )
    own = write(folder / 'Own.cfc')
    inside = write(folder / 'lib' / 'in' / 'In.cfc')
    outside = write(tmp_path / 'shared' / 'Shared.cfc')

    discovery = discover(str(folder), 100)

    assert discovery == Discovery(
        sorted([own, inside, outside]),
        [(folder / 'lib' / 'in').as_posix(), (tmp_path / 'shared').as_posix()],
        'walk',
        None,
    )


def test_walk_stops_at_the_cap(tmp_path):
    folder = tmp_path / 'folder'
    write(folder / 'server.json', '{}')
    for index in range(10):
        write(folder / f'C{index}.cfc')

    assert discover(str(folder), 3) == Discovery(
        [], [], 'walk', 'more than 3 component files'
    )


def test_walk_stops_after_too_many_entries(tmp_path, monkeypatch):
    folder = tmp_path / 'folder'
    write(folder / 'server.json', '{}')
    for index in range(20):
        write(folder / f'page{index}.cfm', '<p>')
    monkeypatch.setattr(project_files, 'MAX_WALK_ENTRIES', 10)

    discovery = discover(str(folder), 100)

    assert discovery.files == []
    assert discovery.source == 'walk'
    assert discovery.reason == 'more than 10 files and folders to look at'


def test_git_not_on_the_path_means_not_a_git_folder(tmp_path, monkeypatch):
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'tmp/\n')
    user = write(site / 'User.cfc')
    cached = write(site / 'tmp' / 'Cached.cfc')
    monkeypatch.setattr(project_files, 'GIT', 'cfml-test-no-such-git')

    assert discover(str(site), 100).source == 'none'

    write(site / 'Application.cfc')
    application = (site / 'Application.cfc').as_posix()
    assert discover(str(site), 100) == Discovery(
        sorted([user, cached, application]), [], 'walk', None
    )


def test_git_timing_out_means_not_a_git_folder(tmp_path, monkeypatch):
    site = git_repo(tmp_path / 'site')
    write(site / 'User.cfc')

    def run(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs['timeout'])

    monkeypatch.setattr(project_files.subprocess, 'run', run)

    assert discover(str(site), 100).source == 'none'


def test_missing_folder(tmp_path):
    discovery = discover(str(tmp_path / 'missing'), 100)

    assert discovery.files == []
    assert discovery.source == 'none'
    assert discovery.reason


@pytest.fixture
def git_site(tmp_path):
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'tmp/\n')
    write(site / 'box.json', json.dumps({'installPaths': {'dep': 'tmp/dep'}}))
    write(site / 'Own.cfc')
    write(site / 'tmp' / 'dep' / 'Dep.cfc')
    return site


def test_covers_files_git_does_not_ignore(git_site):
    discovery = discover(str(git_site), 100)
    folder = str(git_site)

    assert covers(folder, discovery, (git_site / 'Own.cfc').as_posix())
    # files that do not exist, as when one was just deleted
    assert covers(folder, discovery, (git_site / 'model' / 'New.cfc').as_posix())
    assert covers(folder, discovery, (git_site / 'mé dir' / 'Ü n.cfc').as_posix())
    # git decides, not the rules of the walk
    assert covers(folder, discovery, (git_site / '.config' / 'Dot.cfc').as_posix())
    assert not covers(folder, discovery, (git_site / 'tmp' / 'Other.cfc').as_posix())
    assert not covers(folder, discovery, (git_site / 'tmp' / 'é x.cfc').as_posix())
    assert not covers(folder, discovery, (git_site.parent / 'Out.cfc').as_posix())
    assert not covers(
        folder, discovery, (git_site.parent / 'site2' / 'Out.cfc').as_posix()
    )


def test_covers_files_under_an_install_path(git_site):
    discovery = discover(str(git_site), 100)
    folder = str(git_site)

    assert covers(folder, discovery, (git_site / 'tmp/dep/New.cfc').as_posix())
    assert covers(folder, discovery, (git_site / 'tmp/dep/a/B.cfc').as_posix())
    assert not covers(
        folder, discovery, (git_site / 'tmp/dep/node_modules/B.cfc').as_posix()
    )
    assert not covers(folder, discovery, (git_site / 'tmp/dep/.x/B.cfc').as_posix())


def test_covers_files_of_a_walked_folder(tmp_path):
    folder = tmp_path / 'folder'
    write(folder / 'Application.cfc')
    discovery = discover(str(folder), 100)

    assert covers(str(folder), discovery, (folder / 'model' / 'New.cfc').as_posix())
    assert not covers(
        str(folder), discovery, (folder / 'node_modules' / 'X.cfc').as_posix()
    )
    assert not covers(str(folder), discovery, (folder / '.git' / 'X.cfc').as_posix())
    assert not covers(str(folder), discovery, (tmp_path / 'Out.cfc').as_posix())


def test_covers_nothing_when_nothing_is_listed(tmp_path, git_site):
    over_cap = discover(str(git_site), 1)
    assert not covers(str(git_site), over_cap, (git_site / 'Own.cfc').as_posix())
    assert not covers(str(git_site), over_cap, (git_site / 'tmp/dep/D.cfc').as_posix())

    folder = tmp_path / 'folder'
    write(folder / 'User.cfc')
    none = discover(str(folder), 100)
    assert not covers(str(folder), none, (folder / 'User.cfc').as_posix())


def test_display_path(monkeypatch):
    monkeypatch.setattr(project_files, 'HOME', None)
    folders = ('/site',)
    assert project_files.display_path(folders, '/site/a/B.cfc') == 'a/B.cfc'
    assert project_files.display_path(folders, '/other/B.cfc') == '/other/B.cfc'
    assert project_files.display_path(folders, '/sites/B.cfc') == '/sites/B.cfc'
    assert project_files.display_path((), '/site/B.cfc') == '/site/B.cfc'
    # with several folders, after the name of the deepest one the file is in
    folders = ('/site', '/site/lib', '/vendor')
    assert project_files.display_path(folders, '/site/a/B.cfc') == 'site/a/B.cfc'
    assert project_files.display_path(folders, '/site/lib/B.cfc') == 'lib/B.cfc'
    assert project_files.display_path(folders, '/vendor/B.cfc') == 'vendor/B.cfc'


def test_display_path_shows_the_home_folder_as_a_tilde(monkeypatch):
    monkeypatch.setattr(project_files, 'HOME', '/home/me')
    folders = ('/home/me/site',)
    assert project_files.display_path(folders, '/home/me/lib/B.cfc') == '~/lib/B.cfc'
    assert project_files.display_path((), '/home/me/lib/B.cfc') == '~/lib/B.cfc'
    # the folder the file is in comes first
    assert project_files.display_path(folders, '/home/me/site/B.cfc') == 'B.cfc'
    assert project_files.display_path(folders, '/home/meat/B.cfc') == '/home/meat/B.cfc'
    assert project_files.display_path(folders, '/opt/B.cfc') == '/opt/B.cfc'


@pytest.mark.parametrize(
    ('expanded', 'home'),
    [('/home/me', '/home/me'), ('/home/me/', '/home/me'), ('/', None), ('~', None)],
)
def test_home_folder(monkeypatch, expanded, home):
    monkeypatch.setattr(project_files.os.path, 'expanduser', lambda path: expanded)
    assert project_files.home_folder() == home
