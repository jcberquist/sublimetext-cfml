import sys
from unittest import mock

import pytest

from CFML.src import buffer_metadata, utils, view_state


@pytest.fixture
def listeners():
    # the plugin's own listener lives in cfml_plugin, whose import needs
    # CFML.src to be the real package (its __init__ loads every provider)
    # rather than the test stand-in; the import is undone afterwards, so
    # that tests importing with stand-in providers are not affected
    with mock.patch.dict(sys.modules):
        del sys.modules['CFML.src']
        from CFML import cfml_plugin

    return [
        cfml_plugin.CfmlViewListener,
        buffer_metadata.BufferMetadata,
        view_state.ViewState,
    ]


def test_listeners_apply_to_views_with_the_cfml_syntaxes(listeners):
    for syntax in [
        'Packages/CFML/syntaxes/CFML.sublime-syntax',
        'Packages/CFML/syntaxes/CFScript (CFML).sublime-syntax',
    ]:
        for listener in listeners:
            assert listener.is_applicable({'syntax': syntax}), listener

    for syntax in [
        # the syntax that the top-level ones extend, never assigned to a view
        'Packages/CFML/syntaxes/CFScript (CFML) Base.sublime-syntax',
        'Packages/CFML/syntaxes/HTML (CFML).sublime-syntax',
        'Packages/HTML/HTML.sublime-syntax',
        'Packages/Other/syntaxes/CFML.sublime-syntax',
        'Packages/Other/syntaxes/CFScript (CFML).sublime-syntax',
        None,
    ]:
        for listener in listeners:
            assert not listener.is_applicable({'syntax': syntax}), listener


def test_the_listeners_share_the_view_check():
    assert utils.is_cfml_view({'syntax': 'Packages/CFML/syntaxes/CFML.sublime-syntax'})
    assert not utils.is_cfml_view({'syntax': 'Packages/HTML/HTML.sublime-syntax'})
