import plistlib
from pathlib import Path

import pytest

from scope_selectors import CFML_SCRIPT, CFS_SCRIPT, SCRIPT_SCOPES, matches

METADATA = Path(__file__).parent.parent / 'metadata'


def scope(path):
    return plistlib.loads(path.read_bytes())['scope']


@pytest.mark.parametrize(
    'path', sorted(METADATA.glob('*.tmPreferences')), ids=lambda path: path.name
)
def test_preferences_of_script_apply_in_cfs_files(path):
    for script_scope in SCRIPT_SCOPES:
        assert matches(CFML_SCRIPT + script_scope, scope(path)) == matches(
            CFS_SCRIPT + script_scope, scope(path)
        )


def test_folding_applies_to_cfml_and_cfs_files():
    # folding is set for a syntax, by the scope a file of it begins in
    selector = scope(METADATA / 'cfml-fold.tmPreferences')
    assert matches('embedding.cfml', selector)
    assert matches('source.cfml.script', selector)
