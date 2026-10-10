import pytest

from CFML.src.providers.testbox.testbox_spec_outline import TestboxSpecOutlineCommand

from scope_selectors import matches


class View:
    """a view without specs, which records the scopes it is searched for"""

    def __init__(self, scope):
        self.scope = scope
        self.searched = []

    def match_selector(self, pt, selector):
        return matches(self.scope, selector)

    def sel(self):
        return []

    def viewport_position(self):
        return (0, 0)

    def find_by_selector(self, selector):
        self.searched.append(selector)
        return []


def outline(scope):
    command = TestboxSpecOutlineCommand()
    command.view = View(scope)
    command.run(None)
    return command.view.searched


@pytest.mark.parametrize(
    'scope', ['embedding.cfml text.html.cfml', 'source.cfml.script']
)
def test_specs_are_looked_for_in_cfml_and_cfs_files(scope):
    assert outline(scope)


def test_specs_are_not_looked_for_in_other_files():
    assert not outline('text.plain')
