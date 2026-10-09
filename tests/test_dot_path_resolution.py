import json

import pytest
from index_helpers import add_project, git_repo, write

from CFML.src.component_index.dot_paths import Resolution, cased_dot_path

COPY = 'component { function get() {} function set() {} }'


@pytest.fixture(autouse=True)
def uses_git(git_environment):
    pass


def make_site(tmp_path):
    """
    A git folder with its own components, dependencies installed into the
    ignored lib folder, and a TestBox stub of coldbox/system.
    """
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\n')
    install_paths = {
        name: 'lib/' + name
        for name in ['coldbox', 'testbox', 'cbauth', 'cbi18n', 'cbcsrf']
    }
    write(site / 'box.json', json.dumps({'installPaths': install_paths}))
    for path in [
        'Base.cfc',
        'handlers/Main.cfc',
        'handlers/Base.cfc',
        'models/BaseEntity.cfc',
        'models/query.cfc',
        'modules/contentbox/models/BaseEntity.cfc',
        'services/Mailer.cfc',
        'fw1/one.cfc',
        'lib/coldbox/system/EventHandler.cfc',
        'lib/testbox/tests/resources/coldbox/system/EventHandler.cfc',
    ]:
        # each its own component, not a copy of another
        name = path[:-4].replace('/', '_')
        write(site / path, 'component { function ' + name + '() {} }')
    # cbstorages, installed three times as a nested dependency
    for module in ['cbauth', 'cbi18n', 'cbcsrf']:
        path = site / 'lib' / module / 'modules' / 'cbstorages' / 'models'
        write(path / 'CookieStorage.cfc', COPY)
    return site


@pytest.fixture
def site(tmp_path, index):
    return make_site(tmp_path)


def resolve(index, project_name, dot_path, from_file=None):
    # the resolution, with paths relative to the folder of the window
    resolution = index.resolve_dot_path(project_name, dot_path, from_file)
    root = index.get_project(project_name).folders[0] + '/'
    return resolution._replace(
        file_paths=[path.replace(root, '') for path in resolution.file_paths]
    )


def test_rule_1_relative_to_the_file_comes_first(site, index):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    # not Base.cfc at the root, which rule 3 gives
    assert resolve(index, project_name, 'Base', main) == Resolution(
        ['handlers/Base.cfc'], False, 1
    )
    assert resolve(index, project_name, 'base') == Resolution(['Base.cfc'], False, 3)


def test_rule_2_the_mappings_of_the_project_file_come_next(site, index):
    # a project file without cfc_folders still has its mappings
    mappings = [{'mapping': '/models', 'path': 'modules/contentbox/models'}]
    project_file = site / 'site.sublime-project'
    project_name = add_project([site], {'mappings': mappings}, project_file)
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    # not models/BaseEntity.cfc from the root
    assert resolve(index, project_name, 'models.BaseEntity', main) == Resolution(
        ['modules/contentbox/models/BaseEntity.cfc'], False, 2
    )
    # and rule 1 before it
    assert resolve(index, project_name, 'Main', main) == Resolution(
        ['handlers/Main.cfc'], False, 1
    )


def test_rule_3_from_each_folder_of_the_window(site, index, tmp_path):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    # not the BaseEntity of contentbox, whose chain also ends in models
    assert resolve(index, project_name, 'models.BaseEntity', main) == Resolution(
        ['models/BaseEntity.cfc'], False, 3
    )

    # each folder of the window is a root
    other = git_repo(tmp_path / 'other')
    write(other / 'models' / 'BaseEntity.cfc', 'component { function other() {} }')
    project_name = add_project([site, other])
    resolution = index.resolve_dot_path(project_name, 'models.BaseEntity', main)
    assert resolution == Resolution(
        [
            (site / 'models' / 'BaseEntity.cfc').as_posix(),
            (other / 'models' / 'BaseEntity.cfc').as_posix(),
        ],
        False,
        3,
    )


def test_rule_4_a_folder_chain_anywhere(site, index):
    project_name = add_project([site])

    # not models/BaseEntity.cfc, which has the same file name
    assert resolve(index, project_name, 'contentbox.models.BaseEntity') == Resolution(
        ['modules/contentbox/models/BaseEntity.cfc'], False, 4
    )
    # in any case
    assert resolve(index, project_name, 'CONTENTBOX.models.baseentity') == (
        Resolution(['modules/contentbox/models/BaseEntity.cfc'], False, 4)
    )


def test_rule_4_for_a_single_segment_is_a_guess(site, index):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    assert resolve(index, project_name, 'Mailer', main) == Resolution(
        ['services/Mailer.cfc'], True, 4
    )


def test_a_built_in_component_is_not_guessed(site, index):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    for name in ['Query', 'query', 'http', 'Mail', 'ftp', 'storedproc', 'pdf']:
        assert resolve(index, project_name, name, main) == Resolution([])
    # but it is found by a longer path
    assert resolve(index, project_name, 'models.query', main) == Resolution(
        ['models/query.cfc'], False, 3
    )


def test_rule_5_the_file_name_alone_is_a_guess(site, index):
    project_name = add_project([site])

    # the /framework mapping of FW/1 is a folder named fw1
    assert resolve(index, project_name, 'framework.one') == Resolution(
        ['fw1/one.cfc'], True, 5
    )
    # several, ranked
    assert resolve(index, project_name, 'model.BaseEntity') == Resolution(
        ['models/BaseEntity.cfc', 'modules/contentbox/models/BaseEntity.cfc'],
        True,
        5,
    )


def test_nothing_matches(site, index):
    project_name = add_project([site])

    assert resolve(index, project_name, 'Missing') == Resolution([])
    assert resolve(index, project_name, 'a.b.Missing') == Resolution([])
    assert resolve(index, project_name, '') == Resolution([])
    assert resolve(index, project_name, None) == Resolution([])


def test_the_testbox_stub_comes_after_the_shallower_coldbox(site, index):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    assert resolve(index, project_name, 'coldbox.system.EventHandler', main) == (
        Resolution(
            [
                'lib/coldbox/system/EventHandler.cfc',
                'lib/testbox/tests/resources/coldbox/system/EventHandler.cfc',
            ],
            False,
            4,
        )
    )


def test_identical_copies_resolve_to_one(site, index):
    project_name = add_project([site])

    assert resolve(index, project_name, 'cbstorages.models.CookieStorage') == (
        Resolution(['lib/cbauth/modules/cbstorages/models/CookieStorage.cfc'], False, 4)
    )


def test_extends_resolves_through_the_rules(site, index):
    handler = write(
        site / 'handlers' / 'Users.cfc',
        'component extends="coldbox.system.EventHandler" {}',
    )
    application = write(
        site / 'Application.cfc', 'component extends="framework.one" {}'
    )
    project_name = add_project([site])

    completions = index.get_completions_by_file_path(project_name, handler)
    assert [c.name for c in completions['functions']] == [
        'lib_coldbox_system_EventHandler'
    ]
    completions = index.get_completions_by_file_path(project_name, application)
    assert [c.name for c in completions['functions']] == ['fw1_one']


def test_a_component_does_not_extend_itself(site, index):
    project_name = add_project([site])
    entity = (site / 'models' / 'BaseEntity.cfc').as_posix()
    contentbox = (
        site / 'modules' / 'contentbox' / 'models' / 'BaseEntity.cfc'
    ).as_posix()

    # by file name, this file would come first
    assert index.resolve_path(project_name, entity, 'cborm.models.BaseEntity') == (
        contentbox
    )
    # from the root it is only this file, so the folder chain is next
    assert index.resolve_path(project_name, entity, 'models.BaseEntity') == contentbox
    mailer = (site / 'services' / 'Mailer.cfc').as_posix()
    assert index.resolve_path(project_name, mailer, 'Mailer') is None


def test_a_project_with_cfc_folders_resolves_only_by_folder_and_mapping(site, index):
    project_file = site / 'site.sublime-project'
    data = {
        'cfc_folders': [{'path': 'handlers'}, {'path': 'models'}, {'path': 'fw1'}],
        'mappings': [{'mapping': '/model', 'path': 'models'}],
    }
    project_name = add_project([site], data, project_file)
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    assert resolve(index, project_name, 'Base', main) == Resolution(
        ['handlers/Base.cfc'], False, 1
    )
    assert resolve(index, project_name, 'model.BaseEntity', main) == Resolution(
        ['models/BaseEntity.cfc'], False, 2
    )
    # no folder of the window as root, no folder chain, no file name
    for dot_path in ['models.BaseEntity', 'handlers.Base', 'framework.one', 'one']:
        assert resolve(index, project_name, dot_path, main) == Resolution([])


def test_the_dot_path_is_cased_as_the_file_it_resolved_to():
    file_path = '/site/modules/contentbox/models/BaseEntity.cfc'
    assert cased_dot_path(file_path, 'contentbox.MODELS.baseentity') == (
        'contentbox.models.BaseEntity'
    )
    assert cased_dot_path('/site/fw1/one.cfc', 'framework.one') == 'fw1.one'
    assert cased_dot_path('/site/models/User.cfc', 'user') == 'User'
