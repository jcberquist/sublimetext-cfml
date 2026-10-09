import json
import re
from pathlib import Path

import pytest

from scope_selectors import CFML_SCRIPT, CFS_SCRIPT, SCRIPT_SCOPES, matches

ROOT = Path(__file__).parent.parent


def load_json_with_comments(relative_path):
    text = (ROOT / relative_path).read_text(encoding='utf-8')
    return json.loads(re.sub(r'^\s*//.*$', '', text, flags=re.M))


def applies(binding, scope):
    """Returns whether the selectors of a binding's context match a scope."""
    for context in binding.get('context', []):
        if context['key'] != 'selector':
            continue
        matched = matches(scope, context['operand'])
        if matched != (context.get('operator', 'equal') == 'equal'):
            return False
    return True


def binding_ids(bindings):
    return [
        '+'.join(binding.get('keys', binding.get('modifiers', [])))
        + ' '
        + binding['command']
        for binding in bindings
    ]


KEY_BINDINGS = load_json_with_comments('inputmaps/Default.sublime-keymap')


@pytest.mark.parametrize('binding', KEY_BINDINGS, ids=binding_ids(KEY_BINDINGS))
def test_key_bindings_of_script_apply_in_cfs_files(binding):
    for scope in SCRIPT_SCOPES:
        assert applies(binding, CFML_SCRIPT + scope) == applies(binding, CFS_SCRIPT + scope)


def test_doc_and_toggle_key_bindings_apply_in_cfs_files():
    commands = {
        binding['command']
        for binding in KEY_BINDINGS
        if applies(binding, CFS_SCRIPT + 'variable.other.readwrite.cfml')
    }
    assert {
        'cfml_inline_documentation',
        'cfml_preview_method',
        'cfml_toggle_controller_view',
    } <= commands
    assert 'cfml_close_tag' not in commands


MOUSE_BINDINGS = load_json_with_comments('inputmaps/Default.sublime-mousemap')


@pytest.mark.parametrize('binding', MOUSE_BINDINGS, ids=binding_ids(MOUSE_BINDINGS))
def test_mouse_bindings_of_script_apply_in_cfs_files(binding):
    for scope in SCRIPT_SCOPES:
        assert applies(binding, CFML_SCRIPT + scope) == applies(binding, CFS_SCRIPT + scope)
    assert applies(binding, CFS_SCRIPT + 'meta.string.cfml string.quoted.double.cfml')


def test_build_system_is_selected_for_cfml_and_cfs_files():
    selector = load_json_with_comments('build/CFML.sublime-build')['selector']
    # the scope a file of each syntax begins in
    assert matches('embedding.cfml', selector)
    assert matches('source.cfml.script', selector)
    assert not matches('text.html.basic', selector)
