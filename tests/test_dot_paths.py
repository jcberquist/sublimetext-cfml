from CFML.src.component_index import dot_paths


def test_a_file_has_every_suffix_of_its_chain():
    user = '/site/modules/contentbox/models/User.cfc'
    suffixes = dot_paths.build_suffixes([user], [('/site', '/site')])
    assert suffixes.files == {
        'user': [user],
        'models.user': [user],
        'contentbox.models.user': [user],
        'modules.contentbox.models.user': [user],
    }
    assert suffixes.folders == {
        'modules': ['/site/modules'],
        'modules.contentbox': ['/site/modules/contentbox'],
        'contentbox': ['/site/modules/contentbox'],
        'modules.contentbox.models': ['/site/modules/contentbox/models'],
        'contentbox.models': ['/site/modules/contentbox/models'],
        'models': ['/site/modules/contentbox/models'],
    }


def test_files_share_a_suffix():
    files = ['/site/models/User.cfc', '/site/lib/auth/models/User.cfc']
    suffixes = dot_paths.build_suffixes(files, [('/site', '/site')])
    assert suffixes.files['models.user'] == files
    assert suffixes.files['auth.models.user'] == files[1:]
    assert suffixes.folders['models'] == ['/site/models', '/site/lib/auth/models']


def test_the_outermost_base_is_used():
    # a folder of the window inside another one
    user = '/site/models/User.cfc'
    bases = [('/site/models', '/site/models'), ('/site', '/site')]
    suffixes = dot_paths.build_suffixes([user], bases)
    assert 'models.user' in suffixes.files


def test_an_install_path_outside_the_folders_starts_with_its_name():
    controller = '/shared/coldbox/system/Controller.cfc'
    bases = dot_paths.get_bases(['/site'], ['/site/lib', '/shared/coldbox'])
    assert bases == [('/site', '/site'), ('/shared/coldbox', '/shared')]
    suffixes = dot_paths.build_suffixes([controller], bases)
    assert 'coldbox.system.controller' in suffixes.files
    assert 'shared.coldbox.system.controller' not in suffixes.files
    assert suffixes.folders['coldbox'] == ['/shared/coldbox']


def test_a_cfc_folder_starts_with_its_name():
    user = '/site/model/User.cfc'
    bases = dot_paths.get_configured_bases(['/site/model'])
    suffixes = dot_paths.build_suffixes([user], bases)
    assert suffixes.files == {'user': [user], 'model.user': [user]}
    assert suffixes.folders == {'model': ['/site/model']}


def test_a_file_under_no_base_is_found_by_its_name():
    user = '/elsewhere/User.cfc'
    suffixes = dot_paths.build_suffixes([user], [('/site', '/site')])
    assert suffixes.files == {'user': [user]}
    assert suffixes.folders == {}


def test_chains_are_lower_case_and_folders_keep_their_case():
    user = '/site/Models/User.cfc'
    suffixes = dot_paths.build_suffixes([user], [('/site', '/site')])
    assert set(suffixes.files) == {'user', 'models.user'}
    assert suffixes.folders == {'models': ['/site/Models']}
