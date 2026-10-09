import json
import types

import pytest
from index_helpers import add_project, git_repo, write

from CFML.src.providers.components import cfc_utils, dot_path_completions

COPY = 'component { function get() {} }'


def init(*names):
    # a component whose constructor has the required arguments
    arguments = ', '.join('required ' + name for name in names)
    return 'component { function init(' + arguments + ') {} }'


@pytest.fixture(autouse=True)
def completions(index, settings, git_environment, monkeypatch):
    # the completions of each project the index publishes, with the
    # required arguments of a constructor
    monkeypatch.setattr(dot_path_completions, 'projects', {})
    monkeypatch.setattr(cfc_utils, 'component_index', index)
    index.subscribe(dot_path_completions.build_project_map)
    settings['cfml_cfc_completions'] = 'required'


@pytest.fixture
def site(tmp_path):
    """
    A git folder with a models folder at its root and in two modules, and
    dependencies installed into the ignored lib folder.
    """
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\n')
    install_paths = {name: 'lib/' + name for name in ['cbauth', 'cbi18n', 'cbcsrf']}
    write(site / 'box.json', json.dumps({'installPaths': install_paths}))
    write(site / 'Application.cfc')
    write(site / 'handlers' / 'Main.cfc')
    write(site / 'handlers' / 'Users.cfc')
    write(site / 'models' / 'User.cfc', init('name'))
    write(site / 'models' / 'UserService.cfc')
    write(site / 'models' / 'security' / 'Role.cfc')
    write(site / 'modules' / 'blog' / 'handlers' / 'Posts.cfc')
    write(site / 'modules' / 'blog' / 'models' / 'Post.cfc', init('title'))
    write(site / 'modules' / 'blog' / 'models' / 'User.cfc', init('blogId'))
    write(site / 'modules' / 'shop' / 'handlers' / 'Orders.cfc')
    write(site / 'modules' / 'shop' / 'models' / 'Post.cfc', init('sku'))
    # folders without a component below them
    write(site / 'views' / 'main' / 'index.cfm', '<p>home</p>')
    write(site / 'modules' / 'blog' / 'views' / 'index.cfm', '<p>blog</p>')
    # cbstorages, installed three times as a nested dependency
    for module in ['cbauth', 'cbi18n', 'cbcsrf']:
        path = site / 'lib' / module / 'modules' / 'cbstorages' / 'models'
        write(path / 'CookieStorage.cfc', COPY)
    return site


def view_of(project_name, file_path=None):
    return types.SimpleNamespace(project_name=project_name, file_path=file_path)


def offered(view, cfc_path, completion_type='path_completions'):
    # the trigger of each completion, with a dot after a folder
    return [
        args[0] + ('.' if args[1] == 'cfc path' else '')
        for args, kwargs in dot_path_completions.get_path_completions(
            view, cfc_path, completion_type
        )
    ]


def contents(view, cfc_path):
    # the snippet of each component in a constructor, by name
    return {
        args[0]: args[2]
        for args, kwargs in dot_path_completions.get_path_completions(
            view, cfc_path, 'constructor_completions'
        )
        if args[1] == 'cfc'
    }


def test_a_folder_name_offers_the_components_of_every_folder_of_that_name(site):
    project_name = add_project([site])
    main = view_of(project_name, (site / 'handlers' / 'Main.cfc').as_posix())

    # the models folders of the root, of both modules and of cbstorages;
    # User is in two of them
    assert offered(main, 'models') == [
        'CookieStorage',
        'Post',
        'User',
        'UserService',
        'security.',
    ]
    # in any case
    assert offered(main, 'MODELS') == offered(main, 'models')


def test_nothing_typed_offers_the_files_next_to_the_view_and_the_root(site):
    project_name = add_project([site])
    main = view_of(project_name, (site / 'handlers' / 'Main.cfc').as_posix())

    # views has no component below it, and lib is under the root
    assert offered(main, '') == [
        'Application',
        'Main',
        'Users',
        'handlers.',
        'lib.',
        'models.',
        'modules.',
    ]
    # a buffer that is not saved has only the root
    assert offered(view_of(project_name), '') == [
        'Application',
        'handlers.',
        'lib.',
        'models.',
        'modules.',
    ]


def test_a_nested_dot_path_offers_what_is_below_it(site):
    project_name = add_project([site])
    main = view_of(project_name, (site / 'handlers' / 'Main.cfc').as_posix())

    # from the root, without its views
    assert offered(main, 'modules.blog') == ['handlers.', 'models.']
    # any folder chain that ends in it
    assert offered(main, 'blog.models') == ['Post', 'User']
    assert offered(main, 'models.security') == ['Role']
    # relative to the folder of the view
    posts = view_of(
        project_name, (site / 'modules' / 'blog' / 'handlers' / 'Posts.cfc').as_posix()
    )
    assert offered(posts, '') == [
        'Application',
        'Posts',
        'handlers.',
        'lib.',
        'models.',
        'modules.',
    ]
    assert (
        offered(view_of(project_name, (site / 'Application.cfc').as_posix()), 'views')
        == []
    )


def test_a_folder_with_no_component_below_it_is_not_offered(site):
    project_name = add_project([site])
    main = view_of(project_name, (site / 'handlers' / 'Main.cfc').as_posix())

    assert 'views.' not in offered(main, '')
    assert 'views.' not in offered(main, 'modules.blog')
    assert offered(main, 'views') == []
    assert offered(main, 'views.main') == []


def test_identical_copies_are_offered_once(site):
    project_name = add_project([site])
    main = view_of(project_name, (site / 'handlers' / 'Main.cfc').as_posix())

    assert offered(main, 'cbstorages.models') == ['CookieStorage']
    assert offered(main, 'lib') == ['cbauth.', 'cbcsrf.', 'cbi18n.']


def test_a_name_that_is_a_folder_and_a_component_is_offered_as_both(site, tmp_path):
    write(site / 'models' / 'Security.cfc')
    project_name = add_project([site])
    main = view_of(project_name, (site / 'handlers' / 'Main.cfc').as_posix())

    assert offered(main, 'models') == [
        'CookieStorage',
        'Post',
        'Security',
        'User',
        'UserService',
        'security.',
    ]


def test_names_are_cased_as_in_the_file_system(site):
    write(site / 'Lib' / 'cbstorages' / 'models' / 'SessionStorage.cfc')
    project_name = add_project([site])
    main = view_of(project_name, (site / 'handlers' / 'Main.cfc').as_posix())

    assert offered(main, 'CBSTORAGES.Models') == ['CookieStorage', 'SessionStorage']
    # a folder of the same name, cased another way, is offered once
    assert [name for name in offered(main, '') if name.lower() == 'lib.'] == ['Lib.']


def test_the_constructor_is_that_of_the_file_the_dot_path_resolves_to(site):
    project_name = add_project([site])
    orders = view_of(
        project_name, (site / 'modules' / 'shop' / 'handlers' / 'Orders.cfc').as_posix()
    )
    posts = view_of(
        project_name, (site / 'modules' / 'blog' / 'handlers' / 'Posts.cfc').as_posix()
    )

    # models.Post is a folder chain in both modules: the files are ranked,
    # and the one that shares the most folders with the view is first
    assert contents(orders, 'models')['Post'] == 'Post(${1:sku})'
    assert contents(posts, 'models')['Post'] == 'Post(${1:title})'
    # models.User is the root's from every view, as the dot path resolves
    # from the root before it looks for folder chains
    assert contents(orders, 'models')['User'] == 'User(${1:name})'
    assert contents(posts, 'models')['User'] == 'User(${1:name})'
    # a component without a constructor
    assert contents(orders, 'models')['UserService'] == 'UserService()'
    # a sibling, before a component of the same name from the root
    write(site / 'modules' / 'blog' / 'handlers' / 'User.cfc', init('handler'))
    project_name = add_project([site])
    posts = view_of(project_name, posts.file_path)
    assert contents(posts, '')['User'] == 'User(${1:handler})'


def test_only_a_constructor_has_arguments(site):
    project_name = add_project([site])
    main = view_of(project_name, (site / 'handlers' / 'Main.cfc').as_posix())

    completions = dot_path_completions.get_path_completions(
        main, 'models', 'path_completions'
    )
    assert [args[2] for args, kwargs in completions] == [
        'CookieStorage',
        'Post',
        'User',
        'UserService',
        'security.',
    ]


class View:
    """A view of the text before the position, all of it in one scope."""

    def __init__(self, text, scope):
        self.text = text
        self.scope = scope

    def match_selector(self, point, selector):
        return selector == self.scope

    def scope_name(self, point):
        return self.scope

    def expand_to_scope(self, point, selector):
        return types.SimpleNamespace(begin=lambda: 0)

    def substr(self, region):
        return self.text[region[0] : region[1]]


def cfml_view(project_name, file_path, text, scope, prefix=''):
    return types.SimpleNamespace(
        view=View(text, scope),
        project_name=project_name,
        file_path=file_path,
        position=len(text),
        prefix=prefix,
    )


def test_an_extends_attribute_offers_names_without_arguments(site):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()
    view = cfml_view(
        project_name,
        main,
        'component extends="',
        'meta.class.inheritance.cfml -entity.other.inherited-class.cfml',
    )

    completions = dot_path_completions.get_tag_attributes(view)
    assert [args[2] for args, kwargs in completions] == [
        'Application',
        'Main',
        'Users',
        'handlers.',
        'lib.',
        'models.',
        'modules.',
    ]


def test_new_offers_the_components_of_every_folder_of_that_name(site):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()
    view = cfml_view(
        project_name, main, 'new models.Us', 'meta.instance.constructor.cfml', 'Us'
    )

    completions = dot_path_completions.get_script_completions(view)
    assert [args[2] for args, kwargs in completions] == [
        'CookieStorage()',
        'Post(${1:title})',
        'User(${1:name})',
        'UserService()',
        'security.',
    ]


def test_a_component_added_is_offered(site, index):
    project_name = add_project([site])
    main = view_of(project_name, (site / 'handlers' / 'Main.cfc').as_posix())
    assert 'Role' not in offered(main, 'models')

    role = write(site / 'models' / 'Role.cfc')
    index.project_event_handler('project_file_updated', project_name, role)
    assert 'Role' in offered(main, 'models')

    index.project_event_handler('project_file_removed', project_name, role)
    assert 'Role' not in offered(main, 'models')


def test_a_project_with_cfc_folders_offers_what_its_mappings_give(site):
    project_file = site / 'site.sublime-project'
    data = {
        'cfc_folders': [{'path': 'handlers'}, {'path': 'models'}, {'path': 'modules'}],
        'mappings': [{'mapping': '/model', 'path': 'models'}],
    }
    project_name = add_project([site], data, project_file)
    main = view_of(project_name, (site / 'handlers' / 'Main.cfc').as_posix())
    user = view_of(project_name, (site / 'models' / 'User.cfc').as_posix())

    # the mapping, and no folder of the window, folder chain or sibling
    assert offered(main, '') == ['model.']
    assert offered(main, 'models') == []
    assert offered(main, 'model') == ['User', 'UserService', 'security.']
    assert offered(main, 'blog.models') == []
    # and what is next to a file in a mapped folder, through its mapping
    assert offered(user, '') == ['model.', 'User', 'UserService', 'security.']
    assert contents(main, 'model') == {
        'User': 'User(${1:name})',
        'UserService': 'UserService()',
    }
