import json
import re

import pytest

from CFML.src import minihtml, utils

from conftest import ROOT

STYLES = {
    'entity.name.function': {'foreground': '#0000ff'},
    'entity.other.attribute-name': {'foreground': '#aa5500', 'italic': True},
    'storage.type': {'foreground': '#00aa00', 'italic': False},
}


# the tints of the close button of a method preview, as Sublime Text has
# them on the close button of its build errors
CLOSE_BUTTON_TINTS = {'#00000018', '#ffffff18'}


class FakeView:
    def __init__(self, font_face='Fira Code'):
        self.font_face = font_face

    def settings(self):
        return {'font_face': self.font_face}

    def style_for_scope(self, scope):
        return STYLES.get(scope, {})


@pytest.fixture(autouse=True)
def templates(monkeypatch):
    # the templates as Sublime Text would load them from the package
    def load_template(relative_path):
        return (ROOT / 'templates' / relative_path).read_text(encoding='utf-8')

    monkeypatch.setattr(utils, 'load_template', load_template)
    minihtml.stylesheet.cache_clear()


def css_classes(css):
    # the classes that the selectors of a stylesheet name
    selectors = re.findall(r'([^{}]+)\{', css)
    return {
        name for selector in selectors for name in re.findall(r'\.([\w-]+)', selector)
    }


def markup_classes(markup):
    return {
        name
        for classes in re.findall(r'class=\\?"([^"\\]+)', markup)
        for name in classes.split()
    }


def page_css(page):
    return page[page.index('<style>') : page.index('</style>')]


def page_content(page):
    return page[page.index('</style>') :]


def doc(**fields):
    return minihtml.Doc('greenish', **fields)


def test_doc_page_has_the_side_color_and_the_scope_styles():
    page = minihtml.doc_page(FakeView(), doc(header='h', body='b'))
    assert page.startswith('<body id="cfml-inline-documentation">')
    css = page_css(page)
    assert (
        'body {\n    background-color: '
        'color(var(--greenish) blend(var(--background) 60%));\n}'
    ) in css
    font = '    font-family: "Fira Code", monospace;\n'
    assert '.entity-name-function {\n' + font + '    color: #0000ff;\n}' in css
    assert '.storage-type {\n' + font + '    color: #00aa00;\n}' in css
    # a scope with a hyphen in its name is styled as the others are
    assert (
        '.entity-other-attribute-name {\n'
        + font
        + '    color: #aa5500;\n    font-style: italic;\n}'
    ) in css
    assert '<h1>h</h1>' in page_content(page)


def test_stylesheets_are_given_without_their_comments():
    assert '/*' in utils.load_template('popup.css')
    for name in ['popup.css', 'phantom.css']:
        css = minihtml.stylesheet(name)
        assert '/*' not in css and '*/' not in css
        assert css.count('{') == css.count('}') == utils.load_template(name).count('{')


def test_every_scope_has_a_rule():
    css = minihtml.scope_css(FakeView())
    assert css_classes(css) == {
        minihtml.scope_class(scope) for scope in minihtml.SCOPES
    }


def test_doc_page_shows_links_one_to_a_line():
    links = [{'href': 'https://a', 'text': 'a'}, {'href': 'https://b', 'text': 'b'}]
    content = page_content(minihtml.doc_page(FakeView(), doc(links=links)))
    assert '<a href="https://a">a</a><br><a href="https://b">b</a>' in content


def test_pagination_is_shown_for_more_than_one_doc():
    view = FakeView()
    assert 'pagination' not in page_content(minihtml.doc_page(view, doc()))

    content = page_content(minihtml.doc_page(view, doc(), 0, 3))
    assert (
        '<div class="pagination"><a href="page_2">Prev</a> 1/3 '
        '<a href="page_1">Next</a></div>'
    ) in content
    content = page_content(minihtml.doc_page(view, doc(), 2, 3))
    assert '<a href="page_1">Prev</a> 3/3 <a href="page_0">Next</a>' in content


def test_page_index_reads_pagination_links_only():
    assert minihtml.page_index('page_0') == 0
    assert minihtml.page_index('page_12') == 12
    assert minihtml.page_index('__go_to_component') is None
    assert minihtml.page_index('https://cfdocs.org/page_1') is None


def test_completion_doc_page_leaves_out_what_is_empty():
    page = minihtml.completion_doc_page(FakeView(), doc(header='h'))
    assert page.startswith('<body id="cfml-completion-doc">')
    # the side color tells where the doc is from, as on a doc popup
    assert 'background-color: color(var(--greenish) blend(' in page_css(page)
    content = page_content(page)
    assert '<h1>h</h1>' in content
    for name in ['arguments', 'description', 'pagination']:
        assert name not in content

    arguments = minihtml.argument_list([('a', 'active'), ('b', 'optional')])
    page = minihtml.completion_doc_page(
        FakeView(), doc(header='h', arguments=arguments, body='about a'), 1, 2
    )
    content = page_content(page)
    assert '<div class="arguments">(<span class="argument-active">a</span>, ' in content
    assert '<div class="description">about a</div>' in content
    assert '<a href="page_0">Next</a>' in content


def test_preview_page_has_a_close_link_before_the_path():
    preview = minihtml.Preview(
        minihtml.path_link('f', '/site/User.cfc', ()), '<div>code</div>'
    )
    page = minihtml.preview_page(FakeView(), preview)
    assert page.startswith('<body id="cfml-method-preview">')
    assert (
        '<div class="link"><a class="close" href="__close__">×</a> '
        '<strong>path</strong>: <a href="f">/site/User.cfc</a></div>'
    ) in page_content(page)
    # a phantom has the page to itself
    assert 'html {\n    margin: 0;' in page_css(page)


def test_argument_states_do_not_share_a_class_with_the_required_badge():
    arguments = minihtml.argument_list([('a', 'required')])
    assert markup_classes(arguments) == {'argument-required'}
    assert markup_classes(minihtml.param_header({'name': 'a', 'required': True})) == {
        'required'
    }


def test_the_markup_only_uses_classes_that_are_styled():
    view = FakeView()
    styled = css_classes(page_css(minihtml.doc_page(view, doc())))
    styled |= css_classes(minihtml.stylesheet('phantom.css'))
    # set apart in the markup, but with no style of their own
    styled |= {'argument-required'}

    pages = [
        minihtml.doc_page(view, doc(body=minihtml.path('f', 'p', ())), 0, 2),
        minihtml.completion_doc_page(view, doc(arguments='a', body='b'), 0, 2),
        minihtml.preview_page(view, minihtml.Preview('l', minihtml.code('c')), 0, 2),
    ]
    builders = [
        minihtml.card(
            minihtml.param_header({'name': 'a', 'type': 't', 'required': True}), 'b'
        ),
        minihtml.card(minihtml.header('a')),
        minihtml.argument_list([('a', 'active'), ('b', 'required'), ('c', 'optional')]),
        minihtml.badges([minihtml.badge('Lucee', 'engine')]),
        minihtml.link('f', 'f', plain=True),
        minihtml.note('from Base.cfc'),
        minihtml.signature('a'),
    ]
    for markup in [page_content(page) for page in pages] + builders:
        assert markup_classes(markup) <= styled

    # the docs that ship as data are markup too
    for path in sorted((ROOT / 'src/providers').glob('*/json/*.json')):
        docs = path.read_text(encoding='utf-8')
        if '"header"' in docs:
            json.loads(docs)
            assert markup_classes(docs) <= styled, path.name


def test_the_colors_come_from_the_color_scheme():
    # no color is written out in the styles: each is a variable of the
    # color scheme, or made from those
    view = FakeView()
    pages = [
        minihtml.doc_page(view, doc()),
        minihtml.completion_doc_page(view, doc()),
        minihtml.preview_page(view, minihtml.Preview()),
    ]
    scope_colors = {style['foreground'] for style in STYLES.values()}
    for page in pages:
        colors = set(re.findall(r'#[0-9a-fA-F]{3,8}\b', page_css(page)))
        assert colors - scope_colors <= CLOSE_BUTTON_TINTS


def test_markup_is_only_written_in_minihtml():
    # the providers build what they show with the functions of minihtml
    tag = re.compile(r'</?(?:a|br|div|em|h[1-6]|li|p|small|span|strong|ul)\b[^<>]*>')
    for path in sorted(ROOT.glob('cfml_plugin.py')) + sorted(ROOT.glob('src/**/*.py')):
        if path.name != 'minihtml.py':
            assert tag.findall(path.read_text(encoding='utf-8')) == [], path


def test_sections_are_titled_alike():
    # the docs that ship as data have the section title of the docs built
    # from a component or from cfdocs
    assert minihtml.section('Arguments') == '<h2>Arguments</h2>'
    titles = set()
    for path in sorted((ROOT / 'src/providers').glob('*/json/*.json')):
        docs = path.read_text(encoding='utf-8')
        if '"header"' in docs:
            titles |= set(re.findall(r'<h\d>.*?</h\d>', docs))
    assert titles == {'<h2>Arguments</h2>'}


def test_prose_is_in_the_system_font_and_code_in_the_font_of_the_view():
    view = FakeView('Fira "Code"')
    pages = [
        minihtml.doc_page(view, doc()),
        minihtml.completion_doc_page(view, doc()),
        minihtml.preview_page(view, minihtml.Preview()),
    ]
    for page in pages:
        css = page_css(page)
        assert (
            'body {\n    margin: 0;\n    padding: 0;\n    font-family: system;' in css
        )
        # the font is named in every rule that the stylesheet marks as code
        assert minihtml.CODE_FONT not in css
        code_rules = minihtml.stylesheet('popup.css').count(minihtml.CODE_FONT)
        assert code_rules >= 6
        assert css.count('font-family: "Fira Code", monospace;') >= code_rules

    # a view with no font of its own
    css = page_css(minihtml.doc_page(FakeView(''), doc()))
    assert '.code {\n    font-family: monospace;' in css


def test_a_signature_in_prose_is_marked_for_the_code_font():
    # .signature takes the code font in popup.css, see the next test
    assert minihtml.signature('a: string') == '<span class="signature">a: string</span>'


def test_code_set_in_prose_is_sized_to_the_prose():
    # the font of a view looks larger than the font of the interface, so
    # code in a sentence is sized in em, and code on its own in rem
    css = minihtml.stylesheet('popup.css')
    assert 'font-family: system;\n    font-size: 1.05rem;' in css
    for name in ['code', 'pre', 'signature']:
        assert f'.{name} {{\n    font-family: $code_font;\n    font-size: 0.9em;' in css
    for selector in ['h1', '.card-header', '.arguments']:
        rule = css[css.index(f'\n{selector} {{') :]
        rule = rule[: rule.index('}')]
        assert re.search(r'font-size: [\d.]+rem;', rule), selector
