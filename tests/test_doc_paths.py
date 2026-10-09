import pytest

from CFML.src import minihtml
from CFML.src.minihtml import PATH_MAX_LENGTH, shorten_path

CONTENTBOX = (
    'modules/contentbox/modules/contentbox-deps/modules/cborm/models/'
    'VirtualEntityService.cfc'
)


def test_a_path_that_fits_is_unchanged():
    assert shorten_path('models/User.cfc') == 'models/User.cfc'
    path = 'models/' + 'u' * 49 + '.cfc'
    assert len(path) == PATH_MAX_LENGTH
    assert shorten_path(path) == path


def test_folders_are_left_out_of_the_middle():
    assert len(CONTENTBOX) == 88
    assert shorten_path(CONTENTBOX) == (
        'modules/\u2026/modules/cborm/models/VirtualEntityService.cfc'
    )
    assert shorten_path(CONTENTBOX, 47) == (
        'modules/\u2026/cborm/models/VirtualEntityService.cfc'
    )
    assert (
        shorten_path(CONTENTBOX, 41) == 'modules/\u2026/models/VirtualEntityService.cfc'
    )
    assert shorten_path(CONTENTBOX, 40) == 'modules/\u2026/VirtualEntityService.cfc'


def test_the_first_folder_comes_before_the_last_ones():
    assert shorten_path('site/a/b/c/User.cfc', 16) == 'site/\u2026/User.cfc'
    assert shorten_path('site/a/b/c/User.cfc', 18) == 'site/\u2026/c/User.cfc'


def test_the_file_name_is_kept_when_nothing_else_fits():
    assert shorten_path(CONTENTBOX, 30) == '\u2026/VirtualEntityService.cfc'
    # a file name longer than the limit on its own is shown whole
    assert shorten_path(CONTENTBOX, 10) == '\u2026/VirtualEntityService.cfc'


def test_a_path_with_one_folder():
    path = 'contentbox-deps/VirtualEntityService.cfc'
    assert shorten_path(path, 30) == '\u2026/VirtualEntityService.cfc'
    # a folder no longer than the ellipsis is kept, as leaving it out
    # would not make the path any shorter
    assert shorten_path('a/VirtualEntityService.cfc', 10) == (
        'a/VirtualEntityService.cfc'
    )


def test_a_file_name_alone_is_unchanged():
    assert shorten_path('VirtualEntityService.cfc', 10) == 'VirtualEntityService.cfc'


def test_absolute_paths_keep_their_root():
    path = '/opt/lib/coldbox/system/web/services/HandlerService.cfc'
    assert shorten_path(path, 40) == '/\u2026/web/services/HandlerService.cfc'
    path = '~/lib/coldbox/system/web/services/HandlerService.cfc'
    assert shorten_path(path, 40) == '~/\u2026/web/services/HandlerService.cfc'
    path = 'C:/lib/coldbox/system/web/services/HandlerService.cfc'
    assert shorten_path(path, 40) == 'C:/\u2026/web/services/HandlerService.cfc'


@pytest.mark.parametrize('max_length', range(30, 90, 5))
def test_a_shortened_path_fits_when_its_file_name_does(max_length):
    shortened = shorten_path(CONTENTBOX, max_length)
    assert len(shortened) <= max_length
    assert shortened.endswith('/VirtualEntityService.cfc')


def test_the_path_line_shows_the_shortened_path_as_text():
    folders = ('/work/R&D',)
    file_path = '/work/R&D/<a>/contentbox-deps/modules/cborm/models/' + (
        'VirtualEntityService.cfc'
    )
    assert minihtml.path_link('f', file_path, folders) == (
        '<strong>path</strong>: '
        '<a href="f">&lt;a&gt;/\u2026/modules/cborm/models/VirtualEntityService.cfc</a>'
    )
    # a folder name of several is shown, escaped, before the path
    folders = ('/work/R&D', '/work/lib')
    assert minihtml.path('__go_to_component', '/work/R&D/User.cfc', folders) == (
        '<div class="path"><strong>path</strong>: '
        '<a href="__go_to_component">R&amp;D/User.cfc</a></div>'
    )
