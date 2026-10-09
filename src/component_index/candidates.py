# Orders the component files that a name could be, wherever a name gives
# several: a dot path that matches more than one folder chain, or a
# variable name that more than one component is given. This module does not
# use the sublime module or the component index, so anything can import it.

import os
from collections.abc import Iterable, Mapping, Sequence

from ..component_parser import ComponentMetadata
from ..project_files import is_under


def rank(
    file_paths: Iterable[str],
    index: Mapping[str, ComponentMetadata],
    install_paths: Sequence[str] = (),
    from_file: str | None = None,
) -> list[str]:
    """
    Returns the files best first, without duplicates and with identical
    copies collapsed into the best ranked one. Files are ranked by:

    1. own source before files under one of the install paths
    2. the most leading folders shared with from_file, the file the name is
       written in, when there is one
    3. the fewest folders in the path
    4. the path, alphabetically without regard to case

    Copies are files with the same name, without regard to case, and equal
    metadata in the index; nested dependencies install the same package
    several times. A file that is not in the index is never a copy.
    """
    from_folders = folders_of(from_file) if from_file else []

    def sort_key(file_path):
        folders = folders_of(file_path)
        return (
            any(is_under(install_path, file_path) for install_path in install_paths),
            -shared_length(folders, from_folders),
            len(folders),
            file_path.lower(),
            file_path,
        )

    ranked = []
    kept: list[tuple[str, ComponentMetadata]] = []
    for file_path in sorted(set(file_paths), key=sort_key):
        metadata = index.get(file_path)
        if metadata is not None:
            name = os.path.basename(file_path).lower()
            if any(name == n and metadata == m for n, m in kept):
                continue
            kept.append((name, metadata))
        ranked.append(file_path)
    return ranked


def folders_of(file_path: str) -> list[str]:
    # the folders of a normalized path, from the root down
    return file_path.split('/')[:-1]


def shared_length(folders: list[str], other: list[str]) -> int:
    length = 0
    for folder, other_folder in zip(folders, other, strict=False):
        if folder != other_folder:
            break
        length += 1
    return length
