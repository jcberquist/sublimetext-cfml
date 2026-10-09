# Resolves the dot path of a component, as in `new a.b.C()`, `extends`,
# `implements` and `createObject("component", "a.b.C")`, to the indexed
# files it can be, with no mappings needed. This module does not use the
# sublime module.
#
# The rules, in order; the first that matches wins and can give several
# files, which are ranked with candidates.rank():
#
# 1. relative to the folder of the file the dot path is written in
# 2. through the `mappings` of the project file
# 3. from each folder of the window, as `/`
# 4. a folder chain of that name anywhere in the index: `contentbox.models.
#    BaseEntity` is any file whose path ends in contentbox/models/
#    BaseEntity.cfc. A single segment (`new Foo()`) is a guess, and is not
#    tried for the names of the components CFML has built in.
# 5. for two or more segments, the file name alone; always a guess, and
#    what finds `framework.one` where the `/framework` mapping is a folder
#    named fw1
#
# Rules 3 to 5 apply to projects whose components are found in the folders
# of their window. A project with `cfc_folders` resolves with rules 1 and 2
# only, as it did before they were added.
#
# The folder chain of a file is its path relative to a base folder, so that
# the chain is as long as can be:
#
# - the outermost folder of the window that the file is in
# - for a file under an install path outside every folder of the window,
#   the parent of the install path, so the chain starts with its name
# - with `cfc_folders`, the parent of the outermost cfc folder that the file
#   is in, so the chain starts with the cfc folder's name

import os
from collections.abc import Iterable
from typing import TYPE_CHECKING, NamedTuple

from ..project_files import is_under
from . import candidates

if TYPE_CHECKING:
    from .index import ComponentProjectData


# CFML's own components, which `new Query()` and the like create
BUILT_IN_COMPONENTS = frozenset(
    ['query', 'http', 'mail', 'ftp', 'storedproc', 'pdf', 'ldap', 'feed']
)


class Resolution(NamedTuple):
    """The files a dot path resolves to."""

    # best first; empty when no rule matched
    file_paths: list[str]
    # whether the files only share a name with the dot path: rule 4 for a
    # single segment, and rule 5
    guessed: bool = False
    # the rule that matched, 1 to 5, or 0
    rule: int = 0


NOT_FOUND = Resolution([])


class Suffixes(NamedTuple):
    """The folder chains of the files of an index."""

    # the component files whose chain, without the extension, ends in each
    # lower case dot path: `models.user` and `user` for models/User.cfc
    files: dict[str, list[str]]
    # the folders, absolute and cased as in the file system, whose chain
    # ends in each lower case dot path
    folders: dict[str, list[str]]


def get_bases(
    folders: Iterable[str], install_paths: Iterable[str]
) -> list[tuple[str, str]]:
    """
    Returns, for a project whose components are found in the folders of its
    window, what build_suffixes() takes: each folder is its own base, and an
    install path outside every folder has its parent as base.
    """
    folders = list(folders)
    bases = [(folder, folder) for folder in folders]
    for install_path in install_paths:
        if not any(is_under(folder, install_path) for folder in folders):
            bases.append((install_path, os.path.dirname(install_path)))
    return bases


def get_configured_bases(root_paths: Iterable[str]) -> list[tuple[str, str]]:
    """Returns the bases of the cfc folders of a project file."""
    return [(root_path, os.path.dirname(root_path)) for root_path in root_paths]


def build_suffixes(file_paths: Iterable[str], bases: list[tuple[str, str]]) -> Suffixes:
    """
    Returns the folder chains of the files. bases are pairs of a folder and
    the folder that the chains of the files under the first are relative
    to; the pair with the outermost base that a file is under is used, and
    a file under none of them has its name as its chain.
    """
    bases = sorted(bases, key=lambda pair: len(pair[1]))
    files: dict[str, list[str]] = {}
    folder_chains: dict[str, list[str]] = {}
    for file_path in file_paths:
        base = next(
            (base for folder, base in bases if is_under(folder, file_path)),
            os.path.dirname(file_path),
        )
        # component files end in .cfc
        parts = file_path[len(base) + 1 : -4].split('/')
        chain = [part.lower() for part in parts]
        for i in range(len(chain)):
            files.setdefault('.'.join(chain[i:]), []).append(file_path)
        folder = base
        for j, part in enumerate(parts[:-1]):
            folder += '/' + part
            if folder not in folder_chains:
                folder_chains[folder] = chain[: j + 1]

    folders: dict[str, list[str]] = {}
    for folder, chain in folder_chains.items():
        for i in range(len(chain)):
            folders.setdefault('.'.join(chain[i:]), []).append(folder)
    return Suffixes(files, folders)


def resolve(
    project_data: ComponentProjectData,
    dot_path: str,
    from_file: str | None = None,
    exclude: str | None = None,
) -> Resolution:
    """
    Returns the files of the index that the dot path resolves to, by the
    first of the rules above that matches, from the file it is written in
    when it is given; an unsaved buffer has none. The excluded file is not
    one of them, as a component does not extend itself, so a rule that
    matches only that file does not match.
    """
    if not dot_path:
        return NOT_FOUND
    key = dot_path.lower()
    relative_path = key.replace('.', '/') + '.cfc'
    file_paths = project_data['file_paths']

    def found(paths, guessed, rule):
        paths = [path for path in paths if path != exclude]
        if not paths:
            return None
        if len(paths) > 1:
            paths = candidates.rank(
                paths, project_data['index'], project_data['install_paths'], from_file
            )
        return Resolution(paths, guessed, rule)

    if from_file:
        path = file_paths.get(os.path.dirname(from_file).lower() + '/' + relative_path)
        if path and (resolution := found([path], False, 1)):
            return resolution

    mapped = project_data['dot_paths'].get(key)
    if mapped and (resolution := found([mapped['file_path']], False, 2)):
        return resolution

    if not project_data['automatic']:
        return NOT_FOUND

    roots = [
        folder.lower() + '/' + relative_path for folder in project_data['discoveries']
    ]
    if resolution := found([file_paths[r] for r in roots if r in file_paths], False, 3):
        return resolution

    suffixes = project_data['file_suffixes']
    if '.' not in key:
        if key in BUILT_IN_COMPONENTS:
            return NOT_FOUND
        return found(suffixes.get(key, []), True, 4) or NOT_FOUND

    file_name = key.rsplit('.', 1)[1]
    return (
        found(suffixes.get(key, []), False, 4)
        or found(suffixes.get(file_name, []), True, 5)
        or NOT_FOUND
    )


def cased_dot_path(file_path: str, dot_path: str) -> str:
    """
    Returns the dot path as it is cased in the file system, from the file
    it resolved to: its last folders and its name, as many as the dot path
    has segments.
    """
    count = dot_path.count('.') + 1
    return '.'.join(file_path[:-4].split('/')[-count:])
