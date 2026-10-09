# Helpers for tests that index real folders in tmp_path, with the git_environment,
# settings and index fixtures of conftest.py.

import subprocess

from CFML.src.project_watcher import Project, project_watcher


def write(path, text='component {}'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path.as_posix()


def git_repo(folder):
    folder.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ['git', '-C', str(folder), 'init', '-q'], check=True, capture_output=True
    )
    return folder


def add_project(folders, data=None, project_file=None):
    """
    Opens a project on the folders, with a project file when given one, and
    returns its name.
    """
    folders = tuple(sorted(folder.as_posix() for folder in folders))
    if project_file is None:
        name = 'folders:' + '|'.join(folders)
        project = Project(name, {}, None, folders)
    else:
        name = project_file.as_posix()
        project = Project(name, data or {}, project_file.parent.as_posix(), folders)
    project_watcher.projects[name] = project
    project_watcher.notify('project_added', name)
    return name
