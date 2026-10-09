import pytest

from CFML.src.cfml_view import CfmlView, ContextType

from scope_selectors import CFML_SCRIPT, CFS_SCRIPT, matches


class View:
    """a view with the given scopes at its points, and plain text elsewhere"""

    def __init__(self, scopes):
        self.scopes = scopes

    def scope_name(self, pt):
        return self.scopes.get(pt, 'text.plain ')

    def match_selector(self, pt, selector):
        return matches(self.scope_name(pt), selector)


def context_type(scopes, pt=10):
    # the type only, without what each type then looks up in the view
    cfml_view = CfmlView.__new__(CfmlView)
    cfml_view.view = View(scopes)
    cfml_view.prefix_start = cfml_view.position = pt
    cfml_view.set_tag_info = lambda tag_in_script=False: None
    cfml_view.set_dot_context = lambda: None
    cfml_view.get_function_call_params = lambda pt: None
    cfml_view.determine_type()
    return cfml_view.type


@pytest.mark.parametrize('script', [CFML_SCRIPT, CFS_SCRIPT])
def test_script_has_the_same_context_in_cfml_and_cfs_files(script):
    assert (
        context_type({10: script + 'variable.other.readwrite.cfml'})
        == ContextType.SCRIPT
    )
    assert (
        context_type(
            {
                9: script + 'punctuation.accessor.cfml',
                10: script + 'meta.property.cfml',
            }
        )
        == ContextType.DOT
    )
    assert (
        context_type(
            {10: script + 'meta.tag.script.cfml entity.other.attribute-name.cfml'}
        )
        == ContextType.TAG_ATTRIBUTES
    )


def test_tags_are_only_in_cfml_files():
    tag = 'embedding.cfml text.html.cfml meta.tag.cfml entity.name.tag.cfml'
    assert context_type({10: tag}) == ContextType.TAG
    assert context_type({10: 'text.plain'}) is None


def test_a_dot_before_the_end_of_a_tag_is_the_dot_context():
    # `<cfset x = y.|>`: the caret is on the `>`, the dot decides
    tag_end = 'embedding.cfml text.html.cfml meta.tag.cfml punctuation.definition.tag.end.cfml'
    assert (
        context_type({9: CFML_SCRIPT + 'punctuation.accessor.cfml', 10: tag_end})
        == ContextType.DOT
    )


def test_a_script_tag_before_the_end_of_its_statement_is_the_attributes_context():
    # `http url="x" |;` and `component |{`: the space before the caret is
    # in the tag, what follows is not
    assert (
        context_type(
            {
                9: CFML_SCRIPT + 'meta.tag.script.cfml',
                10: CFML_SCRIPT + 'punctuation.terminator.statement.cfml',
            }
        )
        == ContextType.TAG_ATTRIBUTES
    )
    assert (
        context_type(
            {
                9: CFML_SCRIPT + 'meta.class.declaration.cfml',
                10: CFML_SCRIPT
                + 'meta.class.body.cfml punctuation.section.block.begin.cfml',
            }
        )
        == ContextType.TAG_ATTRIBUTES
    )
    # but not right after an attribute's closing quote
    assert (
        context_type(
            {
                9: CFML_SCRIPT
                + 'meta.tag.script.cfml string.quoted.double.cfml punctuation.definition.string.end.cfml',
                10: CFML_SCRIPT + 'punctuation.terminator.statement.cfml',
            }
        )
        == ContextType.SCRIPT
    )
