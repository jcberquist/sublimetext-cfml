import os
import shutil
import subprocess
import sys
import threading
from functools import partial

import sublime
import sublime_plugin

from .. import utils

# seconds to wait for cfformat before giving up
TIMEOUT = 30


class FormatError(Exception):
    pass


def find_cfformat():
    """
    Returns the path of the cfformat binary, or None when there is none: the
    `cfformat_path` setting is a path to it or a name to find on the PATH.
    """
    cfformat_path = utils.get_setting('cfformat_path') or 'cfformat'
    return shutil.which(os.path.expanduser(cfformat_path))


def startupinfo():
    # as in Default/exec.py: Windows opens a console window for the process
    # unless it is told not to
    if sys.platform != 'win32':
        return None
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return info


def run_cfformat(cfformat, source, path):
    """
    Returns the source as cfformat formats it and the messages cfformat had
    about it. The source is read as if it were the file at the path, which is
    where cfformat gets its settings and its mode (script or tags) from.
    """
    try:
        proc = subprocess.run(
            [cfformat, '--stdin-filepath', path],
            input=source.encode('utf-8'),
            capture_output=True,
            cwd=os.path.dirname(path),
            timeout=TIMEOUT,
            startupinfo=startupinfo(),
        )
    except subprocess.TimeoutExpired:
        raise FormatError(f'no result within {TIMEOUT} seconds') from None
    except OSError as e:
        raise FormatError(str(e)) from None

    # code that cfformat could not format is reported on stderr and left as
    # it was written
    messages = proc.stderr.decode('utf-8', 'replace').strip()
    if proc.returncode != 0:
        raise FormatError(messages or f'exit code {proc.returncode}')

    # cfformat writes the line endings of the OS by default, and the text of
    # a view only has line feeds
    return proc.stdout.decode('utf-8').replace('\r\n', '\n'), messages


class CfmlFormatCommand(sublime_plugin.TextCommand):
    """
    Formats the whole file with cfformat. cfformat runs on a thread of its
    own, so Sublime Text is not held up while it does, and its result is only
    used if the file was not edited in the meantime.
    """

    def run(self, edit, **kwargs):
        # the arguments of the CFScript formatter's command of this name are
        # accepted, so that a key binding left over from it still works
        cfformat = find_cfformat()
        if not cfformat:
            sublime.status_message(
                'CFML: cfformat was not found, see the "cfformat_path" setting'
            )
            return

        view = self.view
        source = view.substr(sublime.Region(0, view.size()))
        threading.Thread(
            target=self.format,
            args=(cfformat, source, self.format_path(), view.change_count()),
            daemon=True,
        ).start()

    def is_enabled(self, **kwargs):
        return self.view.match_selector(0, 'embedding.cfml, source.cfml.script')

    def format_path(self):
        # a view that was never saved is formatted as a .cfc in the first
        # folder of its window: cfformat reads the mode of a .cfc from its
        # source
        file_name = self.view.file_name()
        if file_name:
            return file_name
        window = self.view.window()
        folders = window.folders() if window else []
        folder = folders[0] if folders else os.path.expanduser('~')
        return os.path.join(folder, 'untitled.cfc')

    def format(self, cfformat, source, path, change_count):
        try:
            formatted, messages = run_cfformat(cfformat, source, path)
        except FormatError as e:
            sublime.set_timeout(partial(self.show_error, str(e)))
            return
        sublime.set_timeout(
            partial(self.show_result, source, formatted, messages, change_count)
        )

    def show_error(self, error):
        print('CFML: cfformat failed - ' + error)
        sublime.status_message('CFML: cfformat failed - ' + error.splitlines()[0])

    def show_result(self, source, formatted, messages, change_count):
        view = self.view
        if not view.is_valid():
            return
        if view.change_count() != change_count:
            sublime.status_message(
                'CFML: not formatted, the file was edited while cfformat ran'
            )
            return

        if formatted != source:
            view.run_command('cfml_replace_text', {'text': formatted})

        if messages:
            print('CFML: cfformat - ' + messages)
            sublime.status_message('CFML: cfformat - ' + messages.splitlines()[0])
        elif formatted != source:
            sublime.status_message('CFML: formatted')
        else:
            sublime.status_message('CFML: already formatted')


class CfmlReplaceTextCommand(sublime_plugin.TextCommand):
    """
    Replaces the text of the view, keeping the selections and the scroll
    position. It is run by `cfml_format` once cfformat has finished.
    """

    def run(self, edit, text):
        view = self.view
        selections = [(view.rowcol(sel.a), view.rowcol(sel.b)) for sel in view.sel()]
        viewport = view.viewport_position()

        view.replace(edit, sublime.Region(0, view.size()), text)

        view.sel().clear()
        for a, b in selections:
            view.sel().add(
                sublime.Region(
                    view.text_point(*a, clamp_column=True),
                    view.text_point(*b, clamp_column=True),
                )
            )
        view.set_viewport_position(viewport, False)
