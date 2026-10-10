import webbrowser
import sublime
import sublime_plugin
from functools import partial
from . import utils
from . import cfml_providers
from .cfml_view import CfmlView


def get_cfml_files(cfml_view):
    cfml_files = []

    for p in cfml_providers.providers:
        gotocfmlfile = p.get_goto_cfml_file(cfml_view)
        if gotocfmlfile:
            cfml_files.append(gotocfmlfile)

    return sorted(cfml_files, key=lambda cfml_file: cfml_file.priority, reverse=True)


def open_file_at_symbol(view, file_path, symbol):
    location = utils.find_symbol_location(view.window(), symbol, file_path)
    if location:
        view.window().open_file(
            location.path_encoded_position(),
            sublime.NewFileFlags.ENCODED_POSITION | sublime.NewFileFlags.FORCE_GROUP,
        )
    else:
        # if symbol can't be found in the index, go ahead and open the file
        view.window().open_file(file_path)


def open_cfml_file(view, file_path, symbol):
    if symbol:
        open_file_at_symbol(view, file_path, symbol)
    elif file_path.startswith('http'):
        webbrowser.open_new_tab(file_path)
    else:
        view.window().open_file(file_path)


def on_select(view, choices, index):
    # -1 when the panel is closed without a choice
    if index >= 0:
        open_cfml_file(view, choices[index].file_path, choices[index].symbol)


def goto(view, cfml_file):
    """
    Opens the file, or when it is one of several the goto could be to,
    lets the user choose one of them.
    """
    if len(cfml_file.choices) > 1:
        items = [
            sublime.QuickPanelItem(choice.label, choice.details)
            for choice in cfml_file.choices
        ]
        view.window().show_quick_panel(
            items, partial(on_select, view, cfml_file.choices)
        )
    else:
        open_cfml_file(view, cfml_file.file_path, cfml_file.symbol)


class CfmlGotoFileCommand(sublime_plugin.TextCommand):
    def run(self, edit, event):
        pt = self.view.window_to_text((event['x'], event['y']))
        cfml_view = CfmlView(self.view, pt)
        cfml_files = get_cfml_files(cfml_view)
        if len(cfml_files) > 0:
            goto(self.view, cfml_files[0])

    def want_event(self):
        return True
