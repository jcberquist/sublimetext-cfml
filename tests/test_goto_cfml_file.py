import types

import pytest
from index_helpers import add_project, git_repo, write

from CFML.src import component_reference, goto_cfml_file
from CFML.src.cfml_view import GotoCfmlFile, GotoChoice
from CFML.src.component_reference import ComponentReference
from CFML.src.providers.components import cfc_utils

PRIORITY = component_reference.PRIORITY


class RecordingWindow:
    """A window that records what is opened in it and the panels it shows."""

    def __init__(self):
        self.opened = []
        self.panels = []

    def symbol_locations(self, symbol, source, type):
        # every file declares every symbol; the position names the symbol
        return [
            types.SimpleNamespace(
                path=path, path_encoded_position=lambda path=path: path + ':' + symbol
            )
            for path in self.files
        ]

    def open_file(self, path, flags=0):
        self.opened.append(path)

    def show_quick_panel(self, items, on_select, *args, **kwargs):
        self.panels.append((items, on_select))


class RecordingView:
    def __init__(self, window):
        self._window = window

    def window(self):
        return self._window


@pytest.fixture
def site(tmp_path, index, git_environment, monkeypatch):
    """
    Three components named Env: two that inherit read() from one parent,
    and one with a read() of its own.
    """
    monkeypatch.setattr(component_reference, 'component_index', index)
    site = git_repo(tmp_path / 'site')
    files = types.SimpleNamespace(
        base=write(site / 'shared' / 'BaseEnv.cfc', 'component { function read() {} }'),
        app=write(
            site / 'app' / 'Env.cfc',
            'component extends="shared.BaseEnv" { function write() {} }',
        ),
        # not a copy of app/Env.cfc, which would be left out of its candidates
        util=write(
            site / 'util' / 'Env.cfc',
            'component extends="shared.BaseEnv" { function write() {} function flush() {} }',
        ),
        lib=write(site / 'lib' / 'Env.cfc', 'component { function read() {} }'),
    )
    project_name = add_project([site])
    window = RecordingWindow()
    window.files = list(vars(files).values())
    return types.SimpleNamespace(
        root=site,
        files=files,
        cfml_view=types.SimpleNamespace(view=None, project_name=project_name),
        window=window,
        view=RecordingView(window),
    )


def reference(file_path, function_name=None, candidates=()):
    return ComponentReference(
        file_path, 'Env', function_name, [], candidates=candidates, guessed=True
    )


def goto_of(site, reference):
    return component_reference.get_goto_cfml_file(site.cfml_view, reference)


def test_one_candidate_has_no_choices(site):
    f = site.files
    assert goto_of(site, reference(f.app)) == GotoCfmlFile(f.app, None, PRIORITY)
    assert goto_of(site, reference(f.app, 'read')) == GotoCfmlFile(
        f.base, 'read', PRIORITY
    )


def test_a_component_with_candidates_offers_each_relative_to_the_folder(site):
    f = site.files
    goto = goto_of(site, reference(f.app, None, (f.util, f.lib)))
    assert goto == GotoCfmlFile(
        f.app,
        None,
        PRIORITY,
        (
            GotoChoice('app/Env.cfc', '', f.app, None),
            GotoChoice('util/Env.cfc', '', f.util, None),
            GotoChoice('lib/Env.cfc', '', f.lib, None),
        ),
    )


def test_a_method_is_offered_where_each_candidate_declares_it(site):
    f = site.files
    goto = goto_of(site, reference(f.lib, 'read', (f.app,)))
    assert goto is not None
    assert goto.choices == (
        GotoChoice('lib/Env.cfc', '', f.lib, 'read'),
        GotoChoice('app/Env.cfc', 'inherited from shared/BaseEnv.cfc', f.base, 'read'),
    )


def test_candidates_that_inherit_the_method_from_one_parent_are_one_choice(site):
    f = site.files
    # both open BaseEnv at read(), so there is nothing to choose
    goto = goto_of(site, reference(f.app, 'read', (f.util,)))
    assert goto == GotoCfmlFile(f.base, 'read', PRIORITY)

    goto = goto_of(site, reference(f.app, 'read', (f.util, f.lib)))
    assert goto is not None
    assert [choice.label for choice in goto.choices] == ['app/Env.cfc', 'lib/Env.cfc']


def test_a_candidate_that_lacks_the_method_is_left_out(site):
    f = site.files
    goto = goto_of(site, reference(f.app, 'write', (f.lib,)))
    assert goto == GotoCfmlFile(f.app, 'write', PRIORITY)

    goto = goto_of(site, reference(f.app, 'write', (f.lib, f.util)))
    assert goto is not None
    assert [choice.file_path for choice in goto.choices] == [f.app, f.util]


def test_details_are_markup_and_labels_are_text(site):
    weird = site.root / 'we<ird&'
    base = write(weird / 'Base.cfc', 'component { function read() {} }')
    env = write(weird / 'Env.cfc', 'component extends="Base" {}')
    project_name = add_project([site.root])
    site.cfml_view.project_name = project_name

    goto = goto_of(site, reference(env, 'read', (site.files.lib,)))
    assert goto is not None
    assert goto.choices[0] == GotoChoice(
        'we<ird&/Env.cfc', 'inherited from we&lt;ird&amp;/Base.cfc', base, 'read'
    )


def test_goto_opens_a_file_with_no_choices_directly(site):
    f = site.files
    goto_cfml_file.goto(site.view, GotoCfmlFile(f.app, None, PRIORITY))
    goto_cfml_file.goto(site.view, GotoCfmlFile(f.base, 'read', PRIORITY))
    assert site.window.opened == [f.app, f.base + ':read']
    assert site.window.panels == []


def test_goto_with_choices_shows_them_and_opens_the_one_chosen(site):
    f = site.files
    goto = goto_of(site, reference(f.lib, 'read', (f.app,)))
    assert goto is not None
    goto_cfml_file.goto(site.view, goto)

    assert site.window.opened == []
    [(items, on_select)] = site.window.panels
    assert [(item.trigger, item.details) for item in items] == [
        ('lib/Env.cfc', ''),
        ('app/Env.cfc', 'inherited from shared/BaseEnv.cfc'),
    ]

    # closed without a choice
    on_select(-1)
    assert site.window.opened == []

    on_select(1)
    assert site.window.opened == [f.base + ':read']
    on_select(0)
    assert site.window.opened == [f.base + ':read', f.lib + ':read']


def test_goto_opens_a_url_in_the_browser(site, monkeypatch):
    opened = []
    monkeypatch.setattr(goto_cfml_file.webbrowser, 'open_new_tab', opened.append)
    goto_cfml_file.goto(site.view, GotoCfmlFile('https://cfdocs.org/len', None, 0))
    assert opened == ['https://cfdocs.org/len']
    assert site.window.opened == []


def test_the_command_goes_to_the_first_result(site, monkeypatch):
    f = site.files
    best = goto_of(site, reference(f.app, None, (f.lib,)))
    other = GotoCfmlFile(f.util, None, 0)
    monkeypatch.setattr(goto_cfml_file, 'CfmlView', lambda view, pt: None)
    monkeypatch.setattr(goto_cfml_file, 'get_cfml_files', lambda view: [best, other])

    command = goto_cfml_file.CfmlGotoFileCommand()
    command.view = site.view
    site.view.window_to_text = lambda xy: 0
    command.run(None, {'x': 0, 'y': 0})

    # the panel is the first result's: its choices, nothing opened yet
    [(items, on_select)] = site.window.panels
    assert [item.trigger for item in items] == ['app/Env.cfc', 'lib/Env.cfc']
    assert site.window.opened == []


def test_a_guessed_new_offers_every_component_of_its_name(site, monkeypatch):
    from CFML.src.providers.components import components

    from test_cfc_utils import constructor_view

    monkeypatch.setattr(
        cfc_utils, 'component_index', component_reference.component_index
    )
    f = site.files
    source = 'component { function f() { return new Env(); } }'
    view = constructor_view(site.cfml_view.project_name, f.base, source, 'new Env()')

    goto = components.get_goto_cfml_file(view)
    assert goto is not None
    assert [choice.label for choice in goto.choices] == [
        'app/Env.cfc',
        'lib/Env.cfc',
        'util/Env.cfc',
    ]
