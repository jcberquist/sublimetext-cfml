from CFML.src.component_index.candidates import rank


def metadata(*functions):
    return {
        'accessors': False,
        'persistent': False,
        'extends': None,
        'initmethod': None,
        'entityname': None,
        'functions': {name: {'name': name} for name in functions},
        'properties': {},
    }


LIB = '/site/lib'


def test_own_source_comes_before_an_install_path():
    files = ['/site/lib/cbauth/models/User.cfc', '/site/models/deep/er/User.cfc']
    assert rank(files, {}, [LIB]) == [
        '/site/models/deep/er/User.cfc',
        '/site/lib/cbauth/models/User.cfc',
    ]


def test_the_most_folders_shared_with_the_file_come_first():
    files = ['/site/a/User.cfc', '/site/b/c/User.cfc']
    from_file = '/site/b/c/d/Page.cfc'
    assert rank(files, {}, [], from_file) == ['/site/b/c/User.cfc', '/site/a/User.cfc']
    # and before the shallowest path, but after own source
    assert rank(files, {}, ['/site/b'], from_file) == [
        '/site/a/User.cfc',
        '/site/b/c/User.cfc',
    ]


def test_the_shallowest_path_comes_first():
    # the TestBox stub of coldbox/system
    stub = '/site/lib/testbox/tests/resources/coldbox/system/EventHandler.cfc'
    real = '/site/lib/coldbox/system/EventHandler.cfc'
    files = [stub, real]
    from_file = '/site/handlers/Main.cfc'
    assert rank(files, {}, [LIB + '/coldbox', LIB + '/testbox'], from_file) == [
        real,
        stub,
    ]


def test_then_alphabetically_without_regard_to_case():
    files = ['/site/b/User.cfc', '/site/C/User.cfc', '/site/a/User.cfc']
    assert rank(files, {}) == [
        '/site/a/User.cfc',
        '/site/b/User.cfc',
        '/site/C/User.cfc',
    ]


def test_identical_copies_collapse_into_the_best_ranked():
    # cbstorages installed three times as a nested dependency
    files = [
        '/site/lib/cbauth/modules/cbstorages/models/CookieStorage.cfc',
        '/site/lib/cbi18n/modules/cbstorages/models/CookieStorage.cfc',
        '/site/lib/cbcsrf/modules/cbstorages/models/cookiestorage.cfc',
    ]
    index = {file_path: metadata('get', 'set') for file_path in files}
    assert rank(files, index, [LIB]) == [files[0]]


def test_different_components_of_one_name_are_kept():
    files = ['/site/a/User.cfc', '/site/b/User.cfc', '/site/c/User.cfc']
    index = {
        files[0]: metadata('get'),
        files[1]: metadata('get', 'set'),
        files[2]: metadata('get'),
    }
    # the third is a copy of the first
    assert rank(files, index) == files[:2]


def test_files_of_other_names_are_not_copies():
    files = ['/site/a/User.cfc', '/site/a/Member.cfc']
    index = {file_path: metadata() for file_path in files}
    assert rank(files, index) == ['/site/a/Member.cfc', '/site/a/User.cfc']


def test_a_file_not_in_the_index_is_kept():
    files = ['/site/a/User.cfc', '/site/b/User.cfc']
    assert rank(files, {files[0]: metadata()}) == files


def test_duplicates_are_left_out():
    assert rank(['/site/a/User.cfc'] * 2, {}) == ['/site/a/User.cfc']
