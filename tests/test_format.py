import json
import os
import sys
import threading

import pytest

from CFML.src.commands import format

posix_only = pytest.mark.skipif(
    sys.platform == 'win32', reason='the stand-in for cfformat is a script'
)


@pytest.fixture
def cfformat(tmp_path):
    """
    Returns a function that writes a stand-in for the cfformat binary, a
    Python script with the given body, and returns its path.
    """

    def write(body):
        path = tmp_path / 'bin' / 'cfformat'
        path.parent.mkdir()
        path.write_text(f'#!{sys.executable}\nimport json, os, sys\n{body}\n')
        path.chmod(0o755)
        return str(path)

    return write


@pytest.fixture
def status(monkeypatch):
    messages = []
    monkeypatch.setattr(
        format.sublime, 'status_message', messages.append, raising=False
    )
    return messages


@pytest.fixture
def cfformat_path(monkeypatch):
    # the `cfformat_path` setting, and a PATH without a cfformat of its own
    settings = {'cfformat_path': 'cfformat'}
    monkeypatch.setattr(format.utils, 'get_setting', settings.get)
    monkeypatch.setenv('PATH', '')
    return lambda value: settings.update(cfformat_path=value)


class FakeWindow:
    def __init__(self, folders):
        self._folders = folders

    def folders(self):
        return self._folders


class FakeView:
    def __init__(self, text, file_name=None, window=None):
        self.text = text
        self.changes = 0
        self.commands = []
        self._file_name = file_name
        self._window = window

    def size(self):
        return len(self.text)

    def substr(self, region):
        begin, end = region
        return self.text[begin:end]

    def change_count(self):
        return self.changes

    def file_name(self):
        return self._file_name

    def window(self):
        return self._window

    def is_valid(self):
        return True

    def run_command(self, name, args):
        self.commands.append((name, args))


def run_command(view, monkeypatch, run_cfformat, **args):
    """Runs cfml_format on the view, with a stand-in for the cfformat run."""
    monkeypatch.setattr(format, 'find_cfformat', lambda: '/bin/cfformat')
    monkeypatch.setattr(format, 'run_cfformat', run_cfformat)
    command = format.CfmlFormatCommand()
    command.view = view
    command.run(None, **args)
    for thread in threading.enumerate():
        if thread is not threading.current_thread():
            thread.join(5)


@posix_only
def test_the_source_is_formatted_as_the_file_at_the_path(cfformat, tmp_path):
    binary = cfformat(
        'source = sys.stdin.buffer.read().decode("utf-8")\n'
        'print(json.dumps([sys.argv[1:], os.getcwd(), source]))'
    )
    path = str(tmp_path / 'Üser.cfc')

    formatted, messages = format.run_cfformat(binary, 'component {ü}\n', path)

    assert json.loads(formatted) == [
        ['--stdin-filepath', path],
        str(tmp_path),
        'component {ü}\n',
    ]
    assert messages == ''


@posix_only
def test_messages_come_with_the_result_which_has_line_feeds_only(cfformat, tmp_path):
    binary = cfformat(
        'sys.stdout.buffer.write(b"component {\\r\\n}\\r\\n")\n'
        'sys.stderr.write("User.cfc:2: not formatted: an unmatched run\\n")'
    )

    result = format.run_cfformat(binary, 'component {}', str(tmp_path / 'User.cfc'))

    assert result == ('component {\n}\n', 'User.cfc:2: not formatted: an unmatched run')


@posix_only
def test_a_failed_run_raises_what_cfformat_reported(cfformat, tmp_path):
    binary = cfformat('sys.exit("a settings error")')

    with pytest.raises(format.FormatError, match='a settings error'):
        format.run_cfformat(binary, 'component {}', str(tmp_path / 'User.cfc'))


def test_a_binary_that_cannot_be_run_raises(tmp_path):
    binary = str(tmp_path / 'cfformat')

    with pytest.raises(format.FormatError, match='cfformat'):
        format.run_cfformat(binary, 'component {}', str(tmp_path / 'User.cfc'))


@posix_only
def test_cfformat_is_found_on_the_path_by_default(cfformat, cfformat_path, monkeypatch):
    binary = cfformat('')
    assert format.find_cfformat() is None

    monkeypatch.setenv('PATH', os.path.dirname(binary))
    assert format.find_cfformat() == binary
    # a setting that was set to null
    cfformat_path(None)
    assert format.find_cfformat() == binary


@posix_only
def test_cfformat_is_found_at_the_path_of_the_setting(
    cfformat, cfformat_path, monkeypatch, tmp_path
):
    binary = cfformat('')
    monkeypatch.setenv('HOME', str(tmp_path))

    cfformat_path(binary)
    assert format.find_cfformat() == binary
    cfformat_path('~/bin/cfformat')
    assert format.find_cfformat() == binary
    cfformat_path('~/bin/missing')
    assert format.find_cfformat() is None


def test_the_file_is_formatted_off_the_calling_thread(monkeypatch, status):
    runs = []

    def run_cfformat(cfformat, source, path):
        runs.append((cfformat, source, path, threading.current_thread()))
        return 'component {\n}\n', ''

    view = FakeView('component {}', file_name='/site/User.cfc')
    # the argument of the former command of this name
    run_command(view, monkeypatch, run_cfformat, current_method=False)

    [(cfformat, source, path, thread)] = runs
    assert (cfformat, source, path) == (
        '/bin/cfformat',
        'component {}',
        '/site/User.cfc',
    )
    assert thread is not threading.current_thread()
    assert view.commands == [('cfml_replace_text', {'text': 'component {\n}\n'})]
    assert status == ['CFML: formatted']


def test_a_formatted_file_is_left_alone(monkeypatch, status):
    view = FakeView('component {\n}\n', file_name='/site/User.cfc')
    run_command(view, monkeypatch, lambda cfformat, source, path: (source, ''))

    assert view.commands == []
    assert status == ['CFML: already formatted']


def test_a_file_edited_while_cfformat_ran_is_left_alone(monkeypatch, status):
    def run_cfformat(cfformat, source, path):
        view.changes += 1
        return 'component {\n}\n', ''

    view = FakeView('component {}', file_name='/site/User.cfc')
    run_command(view, monkeypatch, run_cfformat)

    assert view.commands == []
    assert status == ['CFML: not formatted, the file was edited while cfformat ran']


def test_the_first_message_of_cfformat_is_shown(monkeypatch, status, capsys):
    messages = 'User.cfc:2: not formatted: an unmatched run\nUser.cfc:9: not formatted'
    view = FakeView('component {}', file_name='/site/User.cfc')
    run_command(view, monkeypatch, lambda *args: ('component {\n}\n', messages))

    assert view.commands == [('cfml_replace_text', {'text': 'component {\n}\n'})]
    assert status == ['CFML: cfformat - User.cfc:2: not formatted: an unmatched run']
    assert capsys.readouterr().out == f'CFML: cfformat - {messages}\n'


def test_a_failed_run_is_reported(monkeypatch, status):
    def run_cfformat(cfformat, source, path):
        raise format.FormatError('a settings error\nin .cfformat.json')

    view = FakeView('component {}', file_name='/site/User.cfc')
    run_command(view, monkeypatch, run_cfformat)

    assert view.commands == []
    assert status == ['CFML: cfformat failed - a settings error']


def test_a_missing_cfformat_names_the_setting(cfformat_path, status):
    command = format.CfmlFormatCommand()
    command.view = FakeView('component {}', file_name='/site/User.cfc')
    command.run(None)

    assert status == ['CFML: cfformat was not found, see the "cfformat_path" setting']


@pytest.mark.parametrize(
    'window, folder',
    [(FakeWindow(['/site', '/other']), '/site'), (None, os.path.expanduser('~'))],
    ids=['window_folder', 'no_folder'],
)
def test_an_unsaved_view_is_formatted_as_a_cfc(monkeypatch, status, window, folder):
    paths = []

    def run_cfformat(cfformat, source, path):
        paths.append(path)
        return source, ''

    run_command(FakeView('component {}', window=window), monkeypatch, run_cfformat)

    assert paths == [os.path.join(folder, 'untitled.cfc')]
