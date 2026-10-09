from CFML.src.providers.testbox import test_runner


class Window:
    def __init__(self, folders):
        self._folders = folders

    def folders(self):
        return self._folders


def root_for(setting, project_file_dir, directory, folders=()):
    command = test_runner.TestboxCommand(Window(list(folders)))
    command.get_setting = lambda key: setting
    return command.get_tests_root(project_file_dir, directory)


DIRECTORY = '/work/app/tests/specs/billing/'


def test_the_setting_is_relative_to_the_project_file():
    assert root_for('tests', '/work/app', DIRECTORY) == '/work/app/tests/'


def test_an_absolute_setting_is_used_as_is():
    assert root_for('/srv/tests/', None, DIRECTORY) == '/srv/tests/'


def test_the_project_file_directory_is_the_default():
    assert root_for('', '/work/app', DIRECTORY) == '/work/app/'


def test_without_a_project_file_the_window_folder_holding_the_file_is_the_default():
    folders = ['/work/other', '/work/app']
    assert root_for('', None, DIRECTORY, folders) == '/work/app/'


def test_a_window_folder_matches_whole_path_segments_only():
    assert root_for('', None, DIRECTORY, ['/work/ap']) == ''


def test_without_any_root_there_is_none():
    assert root_for('', None, DIRECTORY) == ''
