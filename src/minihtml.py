"""
The markup of what the package shows in popups and phantoms: the doc popup,
the completion doc and the method preview. The providers build the content
they show with the functions below, and the pages put it together with the
styles of templates/popup.css and the colors of the view's color scheme.
"""

import dataclasses
import functools
import re
from dataclasses import dataclass
from html import escape
from typing import Literal, TypedDict

import sublime

from . import project_files, utils


class Link(TypedDict):
    href: str
    text: str


# the hues that Sublime Text derives from the color scheme for minihtml
Hue = Literal[
    'redish',
    'orangish',
    'yellowish',
    'greenish',
    'cyanish',
    'bluish',
    'purplish',
    'pinkish',
]


@dataclass
class Doc:
    """
    What a doc popup or a completion doc shows. The header, body and
    arguments are markup.
    """

    # the color along the side of the doc popup, which tells the docs of
    # one provider from those of another
    accent: Hue
    header: str = ''
    body: str = ''
    # shown under the body, one to a line
    links: list[Link] = dataclasses.field(default_factory=list)
    # the argument list under the header of a completion doc
    arguments: str = ''


@dataclass
class Preview:
    """What a method preview shows, as markup: a link over the code."""

    link: str = ''
    body: str = ''


# the scopes that docs are colored by, as the color scheme colors them in
# the view; span_wrap() gives text the color of one
SCOPES = [
    'constant.language',
    'entity.name.class',
    'entity.name.function',
    'entity.name.tag.cfml',
    'entity.other.attribute-name',
    'entity.other.inherited-class',
    'storage.modifier',
    'storage.type',
    'string.quoted',
    'variable.language',
    'variable.parameter.function',
]

# the href of the link that closes a method preview
CLOSE_HREF = '__close__'
PAGE_HREF_PREFIX = 'page_'
# stands for the font of the view in the stylesheets
CODE_FONT = '$code_font'

# the most characters of a path that the path line of a doc shows, as a
# path does not wrap: a longer one loses folders from its middle. The line
# is in the font of the interface at 1.05rem, about 7 to 8 pixels a
# character at a font_size of 12 to 14, so 60 characters and "path: " fit
# in the 768 pixels of the doc popup at most font sizes, and in 480 pixels
# at the default ones, for a popup that the window makes narrower
PATH_MAX_LENGTH = 60
# what stands for the folders left out of a path
PATH_ELLIPSIS = '\u2026'

CARD_TEMPLATE = """
<div class="card">
    <div class="card-header">{}</div>
    <div class="card-body">{}</div>
</div>
"""

CSS_COMMENT = re.compile(r'/\*.*?\*/\s*', re.S)
CODE_SPAN = re.compile(r'`([^`\n<>]+)`')


def escape_text(txt):
    # for text shown as is, such as names, paths and hints from the user's
    # code; unlike clean_html(), which keeps the entities of cfdocs text,
    # it escapes & too
    return escape(txt, quote=False).replace('\n', '<br>')


def clean_html(txt):
    return (
        txt.replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('\n ', '<br>')
        .replace('\n', '<br>')
    )


def scope_class(scope):
    return scope.replace('.', '-')


def span_wrap(txt, scope):
    # txt is text, not markup; the scope is one of SCOPES
    return '<span class="' + scope_class(scope) + '">' + escape_text(txt) + '</span>'


def header(key, value='', scope=''):
    # the key and value are text, not markup
    html = escape_text(key)
    if len(value):
        html += ': ' + span_wrap(value, scope)
    return '<strong>' + html + '</strong>'


def param_header(param):
    value = param['type'] if 'type' in param and param['type'] else ''
    html = header(param['name'], value, 'storage.type')

    if 'required' in param and param['required']:
        html += ' ' + badge('Required', 'required')
    return html


def badge(text, name):
    # name is the badge's class in the stylesheet
    return '<span class="' + name + '">&nbsp;' + escape_text(text) + '&nbsp;</span>'


def badges(badges):
    return '<div class="engines">' + ''.join(b + '&nbsp;' for b in badges) + '</div>'


def anchor(href, markup, css_class=''):
    attributes = ' class="' + css_class + '"' if css_class else ''
    return '<a' + attributes + ' href="' + href + '">' + markup + '</a>'


def link(href, markup, plain=False):
    # a plain link has the color of the text around it
    return anchor(href, markup, 'plain-link' if plain else '')


def link_list(links):
    return '<br>'.join(link(item['href'], item['text']) for item in links)


def shorten_path(path, max_length=PATH_MAX_LENGTH):
    """
    Returns the path when it has at most max_length characters, and
    otherwise with folders from its middle replaced by an ellipsis: it keeps
    the file name, then the first folder when that fits, then as many of
    the last folders as fit. A file name too long on its own is kept whole.
    """
    if len(path) <= max_length:
        return path
    *folders, name = path.split('/')
    head = folders[:1]
    if len('/'.join([*head, PATH_ELLIPSIS, name])) > max_length:
        head = []
    # at least one folder after the head is left out
    tail = []
    for folder in reversed(folders[len(head) + 1 :]):
        if len('/'.join([*head, PATH_ELLIPSIS, folder, *tail, name])) > max_length:
            break
        tail.insert(0, folder)
    shortened = '/'.join([*head, PATH_ELLIPSIS, *tail, name])
    # as with a file name and one short folder
    return shortened if len(shortened) < len(path) else path


def path_link(href, file_path, folders, plain=False):
    """
    Returns the path line of a doc: the file's path, which is text, as
    project_files.display_path() shows it for the project's folders, cut
    short by shorten_path().
    """
    text = shorten_path(project_files.display_path(folders, file_path))
    return '<strong>path</strong>: ' + link(href, escape_text(text), plain)


def path(href, file_path, folders):
    return '<div class="path">' + path_link(href, file_path, folders) + '</div>'


def path_note(prose, markup=''):
    """
    Returns a line in small type under the path of a doc: the prose, which
    is text, then the markup.
    """
    return (
        '<div class="path"><small><em>'
        + escape_text(prose)
        + '</em>'
        + markup
        + '</small></div>'
    )


def section(title):
    return '<h2>' + title + '</h2>'


def paragraph(markup):
    return '<p>' + markup + '</p>'


def labeled(label, markup):
    return '<em>' + label + ':</em> ' + markup


def lines(markups):
    """Returns the pieces of markup that are not empty, one to a line."""
    return '<br>'.join(markup for markup in markups if markup)


def block(markup):
    return '<div>' + markup + '</div>'


def bullets(items):
    return '<ul><li>' + '</li><li>'.join(items) + '</li></ul>'


def code(markup):
    return '<span class="code">' + markup + '</span>'


def code_spans(markup):
    """Returns the markup with the text it has between backticks as code."""
    return CODE_SPAN.sub(lambda match: code(match.group(1)), markup)


def signature(markup):
    # for the name and type of an argument where the text around it is prose
    return '<span class="signature">' + markup + '</span>'


def note(text):
    return '<small><em>(' + escape_text(text) + ')</em></small>'


def argument_list(arguments):
    """
    Returns the argument list of a completion doc from the name of each
    argument and whether it is 'active', 'required' or 'optional'.
    """
    spans = [
        '<span class="argument-' + state + '">' + escape_text(name) + '</span>'
        for name, state in arguments
    ]
    return '(' + ', '.join(spans) + ')'


def card(header='', body=''):
    html = CARD_TEMPLATE.format(header.strip(), body.strip())
    html = html.replace('<div class="card-header"></div>\n', '')
    if '<div class="card-body"></div>' in html:
        html = html.replace(
            '<div class="card-header">', '<div class="card-header card-header-empty">'
        )
        html = html.replace('<div class="card-body"></div>\n', '')
    return html


def pagination(index, total):
    """Returns the links to the pages before and after, which wrap around."""
    return (
        '<div class="pagination">'
        + link(PAGE_HREF_PREFIX + str((index - 1) % total), 'Prev')
        + ' '
        + str(index + 1)
        + '/'
        + str(total)
        + ' '
        + link(PAGE_HREF_PREFIX + str((index + 1) % total), 'Next')
        + '</div>'
    )


def page_index(href):
    """Returns the index of the page a pagination link is to, if it is one."""
    if href.startswith(PAGE_HREF_PREFIX):
        return int(href[len(PAGE_HREF_PREFIX) :])
    return None


def from_view(view, region=None):
    truncated = False
    if not region:
        region = sublime.Region(0, view.size())

    if region.size() > 5000:
        region = sublime.Region(region.begin(), region.begin() + 5000)
        truncated = True

    region = view.line(region)

    minihtml = '<div class="minihtml-container">'
    minihtml += view.export_to_html(region, minihtml=True)
    if truncated:
        minihtml += '<br><strong>truncated...</strong>'
    minihtml += '</div>'

    return minihtml


@functools.cache
def stylesheet(name):
    # without its comments, which are for the reader of the file
    return CSS_COMMENT.sub('', utils.load_template(name)).strip() + '\n'


def code_font(view):
    """Returns the font of the view, as the value of a font-family."""
    font_face = view.settings().get('font_face')
    if font_face:
        return '"' + font_face.replace('"', '') + '", monospace'
    return 'monospace'


def styles(view, *names):
    """Returns the stylesheets of the names, with code in the font of the view."""
    css = ''.join(stylesheet(name) for name in names)
    return css.replace(CODE_FONT, code_font(view))


def scope_css(view):
    """
    Returns a rule for each of SCOPES with its style in the view, in the
    font of the view: what is colored as code is code.
    """
    css = ''
    font_family = code_font(view)
    for scope in SCOPES:
        style = view.style_for_scope(scope)
        css += '.' + scope_class(scope) + ' {\n'
        css += '    font-family: ' + font_family + ';\n'
        if 'foreground' in style:
            css += '    color: ' + style['foreground'] + ';\n'
        if style.get('italic'):
            css += '    font-style: italic;\n'
        css += '}\n'
    return css


def side_css(accent: Hue):
    # the hue toned down with the background, as it is the body's background
    color = 'color(var(--' + accent + ') blend(var(--background) 60%))'
    return 'body {\n    background-color: ' + color + ';\n}\n'


def page(element_id, css, content):
    # a color scheme can style the page by its id
    return (
        '<body id="'
        + element_id
        + '">\n<style>\n'
        + css
        + '</style>\n'
        + content
        + '\n</body>'
    )


def doc_page(view, doc: Doc, index=0, total=1):
    """Returns the page of a doc popup, for the doc at index of total docs."""
    css = styles(view, 'popup.css') + scope_css(view) + side_css(doc.accent)
    content = (
        '<div class="container">\n'
        + ('<h1>' + doc.header + '</h1>\n')
        + ('<div>' + doc.body + '</div>\n')
        + ('<div>' + link_list(doc.links) + '</div>\n')
        + '</div>'
    )
    if total > 1:
        content += '\n' + pagination(index, total)
    return page('cfml-inline-documentation', css, content)


def completion_doc_page(view, doc: Doc, index=0, total=1):
    css = styles(view, 'popup.css') + scope_css(view) + side_css(doc.accent)
    content = '<div class="completion">\n<h1>' + doc.header + '</h1>\n'
    if doc.arguments:
        content += '<div class="arguments">' + doc.arguments + '</div>\n'
    if doc.body:
        content += '<div class="description">' + doc.body + '</div>\n'
    if doc.links:
        content += '<div>' + link_list(doc.links) + '</div>\n'
    if total > 1:
        content += pagination(index, total) + '\n'
    content += '</div>'
    return page('cfml-completion-doc', css, content)


def preview_page(view, preview: Preview, index=0, total=1):
    css = styles(view, 'popup.css', 'phantom.css')
    content = (
        '<div class="preview">\n'
        + ('<div class="link">' + anchor(CLOSE_HREF, '×', 'close') + ' ')
        + (preview.link + '</div>\n')
        + ('<div>' + preview.body + '</div>\n')
        + '</div>'
    )
    if total > 1:
        content += '\n' + pagination(index, total)
    return page('cfml-method-preview', css, content)
