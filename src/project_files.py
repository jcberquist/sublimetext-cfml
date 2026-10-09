# Finds the component files of a folder of a window that has no cfc_folders
# setting. In a git work tree these are the files git does not ignore, plus
# the dependency folders that the box.json files there install into, since
# those are usually ignored. A folder that is not a git work tree is walked,
# but only when it looks like a CFML project. This module does not use the
# sublime module, so it can be tested outside Sublime Text.

import json
import os
import subprocess
import sys
from typing import NamedTuple

from .component_parser import is_component_file

# the git executable, looked up on the PATH
GIT = 'git'
# seconds to wait for git before treating the folder as not a git work tree
GIT_TIMEOUT = 10
# the files a folder that is not a git work tree needs at its root to be
# walked; matched without regard to case
MARKERS = {
    'box.json',
    'server.json',
    'application.cfc',
    'application.cfm',
    '.cfconfig.json',
}
# folders no walk goes into, besides those whose name starts with a dot
SKIPPED_FOLDERS = {'node_modules'}
# the reason given for a folder that is not a git work tree and has no marker
NO_MARKER = 'not a git work tree and no CFML marker file such as box.json'
# the most files and folders a discovery looks at in its walks, so that a
# folder such as a home directory is not crawled to the end
MAX_WALK_ENTRIES = 100_000


class Discovery(NamedTuple):
    # component files, absolute, normalized
    files: list[str]
    # dependency folders that were walked
    install_paths: list[str]
    # 'git', 'walk' or 'none'
    source: str
    # why nothing is listed, for the console
    reason: str | None


class TooManyFiles(Exception):
    pass


def discover(folder: str, max_files: int) -> Discovery:
    """
    Returns the component files of the folder. Over max_files component
    files, or over MAX_WALK_ENTRIES files and folders walked, nothing is
    listed and the reason says so.
    """
    folder = normalize(folder)
    if not os.path.isdir(folder):
        return Discovery([], [], 'none', 'not a folder')

    listing = git_listing(folder)
    if listing is not None:
        source = 'git'
    elif has_marker(folder):
        source = 'walk'
    else:
        return Discovery([], [], 'none', NO_MARKER)

    found = Found(max_files)
    try:
        if listing is not None:
            box_files = found.add_listing(listing)
        else:
            box_files = found.walk(folder, collect_box_files=True)
        install_paths = find_install_paths(box_files)
        for install_path in install_paths:
            if source == 'walk' and is_walked(folder, install_path):
                continue
            found.walk(install_path)
    except TooManyFiles as e:
        return Discovery([], [], source, str(e))

    return Discovery(sorted(found.files), install_paths, source, None)


def covers(folder: str, discovery: Discovery, file_path: str) -> bool:
    """
    Returns whether a file, which need not exist, is one that the discovery
    of the folder would list if it were a component file: it is under one of
    the install paths, or under the folder and not ignored by git (in a git
    work tree) or not in a folder the walk skips (in a folder that was
    walked). Nothing is covered when the discovery listed nothing.
    """
    if discovery.reason is not None or discovery.source == 'none':
        return False
    folder = normalize(folder)
    file_path = normalize(file_path)

    for install_path in discovery.install_paths:
        if is_walked(install_path, file_path):
            return True

    if not is_under(folder, file_path):
        return False
    if discovery.source == 'walk':
        return is_walked(folder, file_path)
    return not git_ignores(folder, file_path)


class Found:
    """
    The component files found so far, counted against the cap. Walks count
    the files and folders they look at against MAX_WALK_ENTRIES.
    """

    def __init__(self, max_files: int):
        self.max_files = max_files
        self.files: set[str] = set()
        self.entries = 0

    def add_file(self, path: str):
        self.files.add(path)
        if len(self.files) > self.max_files:
            raise TooManyFiles(f'more than {self.max_files} component files')

    def add_listing(self, listing: list[str]) -> list[str]:
        # adds the component files of a git listing and returns its box.json
        # files; a tracked file that was deleted is still listed
        box_files = []
        for path in listing:
            if not os.path.isfile(path):
                continue
            if os.path.basename(path) == 'box.json':
                box_files.append(path)
            elif is_component_file(path):
                self.add_file(path)
        return box_files

    def walk(self, root: str, collect_box_files: bool = False) -> list[str]:
        """
        Adds the component files under root, skipping dot-folders and
        SKIPPED_FOLDERS, and returns the box.json files found when asked to.
        Symbolic links to folders are not followed.
        """
        box_files = []
        folders = [root]
        while folders:
            current = folders.pop()
            try:
                with os.scandir(current) as iterator:
                    entries = list(iterator)
            except OSError:
                continue
            self.entries += len(entries)
            if self.entries > MAX_WALK_ENTRIES:
                raise TooManyFiles(
                    f'more than {MAX_WALK_ENTRIES} files and folders to look at'
                )
            for entry in entries:
                try:
                    is_dir = entry.is_dir(follow_symlinks=False)
                    is_file = not is_dir and entry.is_file()
                except OSError:
                    continue
                path = current + '/' + entry.name
                if is_dir:
                    if not is_skipped(entry.name):
                        folders.append(path)
                elif is_file:
                    if is_component_file(entry.name):
                        self.add_file(path)
                    elif collect_box_files and entry.name == 'box.json':
                        box_files.append(path)
        return box_files


def git_listing(folder: str) -> list[str] | None:
    """
    Returns the absolute paths of the component files and box.json files
    under the folder that git tracks or does not ignore, or None when the
    folder is not in a git work tree or git cannot be run.
    """
    output = run_git(
        folder,
        ['ls-files', '-co', '--exclude-standard', '-z', '--'],
        ['*.cfc', 'box.json', '*/box.json'],
    )
    if output is None:
        return None
    paths = []
    for relative_path in output.split('\0'):
        if relative_path:
            paths.append(folder + '/' + relative_path)
    return paths


def git_ignores(folder: str, file_path: str) -> bool:
    """
    Returns whether git ignores the file. A file in a folder that is not in
    a git work tree, or that git cannot be asked about, is not ignored.
    """
    result = run_git_status(
        folder, ['check-ignore', '-q', '--'], [os.path.relpath(file_path, folder)]
    )
    # 0 when the path is ignored, 1 when it is not, 128 on an error
    return result == 0


def run_git(folder: str, args: list[str], paths: list[str]) -> str | None:
    # returns the output of git, or None when git fails or cannot be run
    result = _run(folder, args, paths)
    if result is None or result.returncode != 0:
        return None
    return result.stdout.decode('utf-8', 'surrogateescape')


def run_git_status(folder: str, args: list[str], paths: list[str]) -> int | None:
    # returns the exit code of git, or None when git cannot be run
    result = _run(folder, args, paths)
    return None if result is None else result.returncode


def _run(folder, args, paths):
    kwargs = {}
    if sys.platform == 'win32':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    try:
        return subprocess.run(
            [GIT, '-C', folder, *args, *paths],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=GIT_TIMEOUT,
            **kwargs,
        )
    except OSError, subprocess.SubprocessError, ValueError:
        return None


def has_marker(folder: str) -> bool:
    try:
        names = os.listdir(folder)
    except OSError:
        return False
    for name in names:
        name = name.lower()
        if name in MARKERS:
            return True
        if name.startswith('server-') and name.endswith('.json'):
            return True
    return False


def find_install_paths(box_files: list[str]) -> list[str]:
    """
    Returns the folders that the installPaths of the box.json files name and
    that exist, each resolved against the folder of its box.json. A folder
    inside another one in the list is left out, since the walk of the other
    one covers it. A box.json that cannot be read is skipped.
    """
    install_paths = set()
    for box_file in box_files:
        try:
            with open(box_file, encoding='utf-8-sig') as f:
                box = json.load(f)
        except OSError, ValueError:
            continue
        if not isinstance(box, dict):
            continue
        paths = box.get('installPaths')
        if not isinstance(paths, dict):
            continue
        box_folder = os.path.dirname(box_file)
        for path in paths.values():
            if not isinstance(path, str) or not path.strip():
                continue
            install_path = normalize(os.path.join(box_folder, path))
            if os.path.isdir(install_path):
                install_paths.add(install_path)

    result = []
    for install_path in sorted(install_paths):
        if not any(is_under(other, install_path) for other in result):
            result.append(install_path)
    return result


def is_skipped(name: str) -> bool:
    return name.startswith('.') or name in SKIPPED_FOLDERS


def is_walked(root: str, path: str) -> bool:
    # whether a walk of root reaches the path
    if not is_under(root, path):
        return False
    relative_path = path[len(root) + 1 :]
    return not any(is_skipped(name) for name in relative_path.split('/')[:-1])


def is_under(root: str, path: str) -> bool:
    # whether the path is in root or a folder under it; both normalized
    if sys.platform == 'win32':
        root, path = root.lower(), path.lower()
    return path.startswith(root + '/')


def normalize(path: str) -> str:
    """
    Returns the path absolute, with forward slashes and without a trailing
    slash, as the package normalizes paths.
    """
    path = os.path.normpath(os.path.abspath(path)).replace('\\', '/')
    if len(path) > 1 and path.endswith('/') and not path.endswith(':/'):
        path = path[:-1]
    return path


def home_folder() -> str | None:
    """
    Returns the user's home folder, normalized, or None when it is not
    known or is the root of a drive, under which every path would be.
    """
    home = os.path.expanduser('~')
    if home == '~':
        return None
    home = normalize(home)
    return None if home.endswith('/') else home


# the folder that display_path() shows as ~
HOME = home_folder()


def display_path(folders: tuple[str, ...], file_path: str) -> str:
    """
    Returns the path of a file as the package shows it: relative to the
    project folder it is in, after the name of that folder when the project
    has several, and the whole path for a file outside every folder, with
    the user's home folder as ~. The folders and the path are normalized.
    """
    containing = [folder for folder in folders if is_under(folder, file_path)]
    if not containing:
        if HOME and is_under(HOME, file_path):
            return '~' + file_path[len(HOME) :]
        return file_path
    folder = max(containing, key=len)
    relative = file_path[len(folder) + 1 :]
    if len(folders) > 1:
        return folder.rsplit('/', 1)[-1] + '/' + relative
    return relative
