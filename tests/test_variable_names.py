import json
import types
from pathlib import Path

import pytest
from index_helpers import add_project, git_repo, write

from CFML.src.component_parser import parse_cfc_file_string
from CFML.src.component_reference import ComponentReference
from CFML.src.providers.components import cfcs, di, variable_names
from CFML.src.utils import Symbol


class Region:
    def __init__(self, begin, end):
        self.a, self.b = begin, end

    def begin(self):
        return self.a

    def end(self):
        return self.b


@pytest.fixture
def names(component_index, monkeypatch):
    # the component index, with the variable names built at each publication
    monkeypatch.setattr(cfcs, 'component_index', component_index)
    monkeypatch.setattr(cfcs, 'projects', {})
    component_index.subscribe(cfcs.build_project_cfcs)
    return component_index


# the metadata of a view whose component has no properties
NO_PROPERTIES = {'properties': {}}


def call_view(
    project_name, receiver, function_name, file_path=None, metadata=NO_PROPERTIES
):
    """A cfml_view in the arguments of `receiver.function_name(`."""
    region = Region(0, len(receiver))
    return types.SimpleNamespace(
        project_name=project_name,
        file_path=file_path,
        view_metadata=metadata,
        function_call_params=types.SimpleNamespace(
            function_name=function_name,
            dot_context=[Symbol(receiver.lower(), False, None, None, region)],
        ),
    )


def method_view(project_name, source, file_path=None, metadata=NO_PROPERTIES):
    """
    A cfml_view of `receiver.method()` with the position on the method:
    enough of a view for variable_names.find_cfc().
    """
    receiver, rest = source.split('.', 1)
    method = rest.split('(', 1)[0]
    name_region = Region(0, len(receiver))
    method_region = Region(len(receiver) + 1, len(receiver) + 1 + len(method))
    args_region = Region(method_region.end(), len(source))
    view = types.SimpleNamespace(
        match_selector=lambda pt, selector: selector == 'meta.function-call.method',
        substr=lambda pt: source[pt],
    )
    return types.SimpleNamespace(
        view=view,
        project_name=project_name,
        file_path=file_path,
        view_metadata=metadata,
        position=method_region.begin(),
        get_function_call=lambda pt: (method.lower(), method_region, args_region),
        get_dot_context=lambda pt: [
            Symbol(receiver.lower(), False, None, None, name_region)
        ],
    )


@pytest.fixture
def configured(tmp_path, project, names):
    # two cfc folders that give the same name to a component each
    write(tmp_path / 'model' / 'UserService.cfc', 'component { function getUser() {} }')
    write(tmp_path / 'lib' / 'UserService.cfc', 'component { function legacy() {} }')
    project_name = project(
        {
            'cfc_folders': [
                {'path': 'model', 'variable_names': ['{cfc}']},
                {'path': 'lib', 'variable_names': ['{cfc}'], 'accessors': False},
            ]
        }
    )
    names.reindex_project(project_name)
    return project_name


def test_a_name_that_two_cfc_folders_give_keeps_both(tmp_path, configured):
    model = (tmp_path / 'model' / 'UserService.cfc').as_posix()
    lib = (tmp_path / 'lib' / 'UserService.cfc').as_posix()

    # ranked by the folders they share with the file, then alphabetically
    assert [c.file_path for c in cfcs.lookup(configured, ['userService'])] == [
        lib,
        model,
    ]
    from_model = (tmp_path / 'model' / 'Order.cfc').as_posix()
    found = cfcs.lookup(configured, ['userService'], from_model)
    assert found == [
        cfcs.CfcInfo('UserService', model, True, False),
        cfcs.CfcInfo('UserService', lib, False, False),
    ]


def test_a_call_keeps_the_components_that_have_the_method(tmp_path, configured):
    model = (tmp_path / 'model' / 'UserService.cfc').as_posix()
    lib = (tmp_path / 'lib' / 'UserService.cfc').as_posix()
    region = (0, len('userService'))

    view = call_view(configured, 'userService', 'getuser')
    assert variable_names.find_call_cfc(view) == ComponentReference(
        model, 'UserService', None, [region]
    )
    view = call_view(configured, 'userService', 'legacy')
    assert variable_names.find_call_cfc(view) == ComponentReference(
        lib, 'UserService', None, [region]
    )

    # none has it, so all are kept; a name in cfc_folders is not a guess
    view = call_view(configured, 'userService', 'missing')
    assert variable_names.find_call_cfc(view) == ComponentReference(
        lib, 'UserService', None, [region], candidates=(model,), guessed=False
    )


def test_a_method_is_found_on_the_component_that_has_it(tmp_path, configured):
    model = (tmp_path / 'model' / 'UserService.cfc').as_posix()

    reference = variable_names.find_cfc(
        method_view(configured, 'userService.getUser()')
    )
    assert reference is not None
    assert reference.file_path == model
    assert reference.function_name == 'getuser'
    assert reference.candidates == ()

    # no component has the method: no reference to it
    view = method_view(configured, 'userService.missing()')
    assert variable_names.find_cfc(view) is None


def test_the_inject_property_list_shows_each_name_once(configured):
    assert cfcs.get_cfc_list(configured) == ['UserService']


@pytest.fixture
def site(tmp_path, git_environment):
    """
    A git folder whose box.json installs into the ignored lib folder: the
    app's own User and a dependency's, and three identical copies of a
    nested dependency.
    """
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\n')
    write(site / 'box.json', json.dumps({'installPaths': {'deps': 'lib/deps'}}))
    write(site / 'Application.cfc', 'component { function onRequest() {} }')
    write(site / 'handlers' / 'Main.cfc')
    write(site / 'models' / 'User.cfc', 'component { function save() {} }')
    write(site / 'services' / 'Mail.cfc', 'component { function send() {} }')
    write(site / 'lib' / 'deps' / 'models' / 'User.cfc', 'component {}')
    for module in ['auth', 'csrf', 'i18n']:
        storage = site / 'lib' / 'deps' / 'modules' / module / 'storages'
        write(storage / 'Token.cfc', 'component { function get() {} }')
    return site


def paths(cfc_infos, root):
    return [c.file_path.replace(root.as_posix() + '/', '') for c in cfc_infos]


def test_every_component_is_named_by_the_templates(site, index, names):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    # {cfc}, and {cfc}{cfc_folder_singularized}
    found = cfcs.lookup(project_name, ['mailService'], main)
    assert found == [
        cfcs.CfcInfo(
            'MailService', (site / 'services' / 'Mail.cfc').as_posix(), True, True
        )
    ]
    assert paths(cfcs.lookup(project_name, ['mail'], main), site) == [
        'services/Mail.cfc'
    ]
    assert paths(cfcs.lookup(project_name, ['userModel'], main), site) == [
        'models/User.cfc',
        'lib/deps/models/User.cfc',
    ]
    # a name the templates give is a guess
    view = call_view(project_name, 'mailService', 'send', main)
    reference = variable_names.find_call_cfc(view)
    assert reference is not None
    assert reference.guessed is True
    assert reference.class_name == 'MailService'


def test_the_own_source_comes_before_a_dependency(site, index, names):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    view = call_view(project_name, 'user', 'missing', main)
    assert variable_names.find_call_cfc(view) == ComponentReference(
        (site / 'models' / 'User.cfc').as_posix(),
        'User',
        None,
        [(0, 4)],
        candidates=((site / 'lib' / 'deps' / 'models' / 'User.cfc').as_posix(),),
        guessed=True,
    )


def test_identical_copies_are_one_candidate(site, index, names):
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    assert paths(cfcs.lookup(project_name, ['token'], main), site) == [
        'lib/deps/modules/auth/storages/Token.cfc'
    ]
    assert paths(cfcs.lookup(project_name, ['tokenStorage'], main), site) == [
        'lib/deps/modules/auth/storages/Token.cfc'
    ]


def test_two_candidates_that_have_the_method_are_both_kept(site, index, names):
    # a second Mail, which has send() from the component it extends
    write(site / 'lib' / 'deps' / 'Base.cfc', 'component { function send() {} }')
    write(site / 'lib' / 'deps' / 'Mail.cfc', 'component extends="Base" {}')
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    found = cfcs.lookup(project_name, ['mail'], main, 'send')
    assert paths(found, site) == ['services/Mail.cfc', 'lib/deps/Mail.cfc']
    reference = variable_names.find_cfc(method_view(project_name, 'mail.send()', main))
    assert reference is not None
    assert reference.file_path == (site / 'services' / 'Mail.cfc').as_posix()
    assert reference.candidates == ((site / 'lib' / 'deps' / 'Mail.cfc').as_posix(),)

    # only the one that has it
    write(site / 'lib' / 'deps' / 'Base.cfc', 'component { function fetch() {} }')
    names.reindex_project(project_name)
    found = cfcs.lookup(project_name, ['mail'], main, 'fetch')
    assert paths(found, site) == ['lib/deps/Mail.cfc']


def test_the_inject_property_list_of_an_automatic_index_shows_each_name_once(
    site, index, names
):
    # User and UserModel are the names of two components each
    project_name = add_project([site])
    assert cfcs.get_cfc_list(project_name) == [
        'ApplicationSite',
        'Mail',
        'MailService',
        'Main',
        'MainHandler',
        'Token',
        'TokenStorage',
        'User',
        'UserModel',
    ]


def test_a_scope_is_not_a_component(site, index, names):
    project_name = add_project([site])
    assert cfcs.lookup(project_name, ['application']) == []
    assert paths(cfcs.lookup(project_name, ['applicationSite']), site) == [
        'Application.cfc'
    ]


def test_an_empty_template_list_gives_no_names(site, index, names, settings):
    settings['cfml_auto_variable_names'] = []
    project_name = add_project([site])
    assert cfcs.get_cfc_list(project_name) == []


def test_a_project_file_sets_the_templates(tmp_path, site, index, names):
    project_name = add_project(
        [site],
        {'cfml_auto_variable_names': ['the{cfc}']},
        tmp_path / 'site.sublime-project',
    )
    assert cfcs.get_cfc_list(project_name) == [
        'theApplication',
        'theMail',
        'theMain',
        'theToken',
        'theUser',
    ]


def test_a_getter_names_a_component(site, index, names):
    project_name = add_project([site])
    getter = Region(0, len('getMailService'))
    view = call_view(project_name, 'mailService', 'send')
    view.function_call_params.dot_context = [
        Symbol('getmailservice', True, getter, None, getter)
    ]
    reference = variable_names.find_call_cfc(view)
    assert reference is not None
    assert reference.file_path == (site / 'services' / 'Mail.cfc').as_posix()
    assert reference.regions == [getter]


def items(completions):
    # the trigger and annotation of each stand-in CompletionItem
    return [(args[0], args[1]) for args, kwargs in completions]


def dot_view(project_name, receiver, file_path=None, metadata=NO_PROPERTIES):
    """A cfml_view after `receiver.`."""
    region = Region(0, len(receiver))
    return types.SimpleNamespace(
        project_name=project_name,
        file_path=file_path,
        view_metadata=metadata,
        dot_context=[Symbol(receiver.lower(), False, None, None, region)],
    )


def test_one_candidate_offers_its_methods_as_before(site, index, names):
    project_name = add_project([site])
    completions = variable_names.get_dot_completions(dot_view(project_name, 'mail'))
    assert items(completions) == [('send', '')]


def test_several_candidates_offer_the_methods_of_each(site, index, names):
    write(site / 'lib' / 'deps' / 'Base.cfc', 'component { function send() {} }')
    write(
        site / 'lib' / 'deps' / 'mail' / 'Mail.cfc',
        'component extends="deps.Base" { function queue() {} }',
    )
    project_name = add_project([site])
    main = (site / 'handlers' / 'Main.cfc').as_posix()

    view = dot_view(project_name, 'mail', main)
    assert items(variable_names.get_dot_completions(view)) == [
        ('send', 'services/Mail'),
        ('queue', 'mail/Mail'),
        ('send', 'mail/Mail'),
    ]


def test_a_configured_name_of_two_components_respects_their_accessors(
    tmp_path, project, names
):
    write(
        tmp_path / 'model' / 'UserService.cfc',
        'component accessors="true" {\n    property name="dsn";\n}',
    )
    write(
        tmp_path / 'lib' / 'UserService.cfc',
        'component accessors="true" {\n'
        '    property name="dsn";\n'
        '    function legacy() {}\n'
        '}',
    )
    project_name = project(
        {
            'cfc_folders': [
                {'path': 'model', 'variable_names': ['{cfc}']},
                {'path': 'lib', 'variable_names': ['{cfc}'], 'accessors': False},
            ]
        }
    )
    names.reindex_project(project_name)
    from_model = (tmp_path / 'model' / 'Order.cfc').as_posix()

    view = dot_view(project_name, 'userService', from_model)
    assert items(variable_names.get_dot_completions(view)) == [
        ('getDsn', 'model/UserService'),
        ('setDsn', 'model/UserService'),
        ('legacy', 'lib/UserService'),
    ]


def view_metadata(index, project_name, file_path):
    """
    The metadata of a view of the file, as buffer_metadata has it: the
    component in the buffer with what it inherits through the index.
    """
    metadata = parse_cfc_file_string(Path(file_path).read_text(encoding='utf-8'))
    return index.extend_metadata(project_name, file_path, metadata)


@pytest.fixture
def wirebox(tmp_path, git_environment):
    """
    A git folder whose box.json installs cbsecurity into the ignored lib
    folder, and a handler that inherits an injected property.
    """
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\n')
    write(
        site / 'box.json',
        json.dumps({'installPaths': {'cbsecurity': 'lib/modules/cbsecurity'}}),
    )
    write(
        site / 'lib' / 'modules' / 'cbsecurity' / 'models' / 'JWTService.cfc',
        'component { function encode(payload) {} }',
    )
    write(site / 'models' / 'UserService.cfc', 'component { function getUser() {} }')
    write(site / 'services' / 'Mail.cfc', 'component { function send() {} }')
    write(
        site / 'handlers' / 'BaseHandler.cfc',
        'component {\n'
        '    property name="jwt" inject="JWTService@cbsecurity";\n'
        '    property name="userService" inject;\n'
        '}',
    )
    write(
        site / 'handlers' / 'Main.cfc',
        'component extends="BaseHandler" {\n'
        '    property name="users" inject="id:UserService@cb";\n'
        '    property name="lazyUsers" inject="provider:id:UserService";\n'
        '    property name="mail" inject="UserService";\n'
        '}',
    )
    return site


@pytest.fixture
def main(wirebox, index, names):
    """The project of the wirebox folder, and a view of its Main handler."""
    project_name = add_project([wirebox])
    file_path = (wirebox / 'handlers' / 'Main.cfc').as_posix()
    return project_name, file_path, view_metadata(names, project_name, file_path)


def test_an_injected_property_offers_the_methods_of_its_bean(main):
    project_name, file_path, metadata = main

    # jwt is not a variable name, and inherited from BaseHandler
    assert cfcs.lookup(project_name, ['jwt']) == []
    view = dot_view(project_name, 'jwt', file_path, metadata)
    assert items(variable_names.get_dot_completions(view)) == [('encode', '')]

    # variables.jwt.
    view.dot_context.append(Symbol('variables', False, None, None, Region(0, 9)))
    assert items(variable_names.get_dot_completions(view)) == [('encode', '')]

    # not in a component that has the property
    view = dot_view(project_name, 'jwt', file_path)
    assert variable_names.get_dot_completions(view) is None


def test_a_method_of_an_injected_property_is_found_on_its_bean(wirebox, main):
    project_name, file_path, metadata = main
    jwt_service = (
        wirebox / 'lib' / 'modules' / 'cbsecurity' / 'models' / 'JWTService.cfc'
    ).as_posix()

    # hover and goto
    view = method_view(project_name, 'jwt.encode()', file_path, metadata)
    reference = variable_names.find_cfc(view)
    assert reference is not None
    assert reference.file_path == jwt_service
    assert reference.class_name == 'JWTService'
    assert reference.function_name == 'encode'
    # the bean is found by a name that the templates give
    assert reference.guessed is True

    # the parameter popup
    view = call_view(project_name, 'jwt', 'encode', file_path, metadata)
    name_region = view.function_call_params.dot_context[0].name_region
    assert variable_names.find_call_cfc(view) == ComponentReference(
        jwt_service, 'JWTService', None, [name_region], guessed=True
    )


def test_the_inject_property_command_adds_nothing_for_an_injected_property(main):
    project_name, file_path, metadata = main

    def property_name(source, metadata):
        view = method_view(project_name, source, file_path, metadata)
        receiver = source.split('.', 1)[0]
        # the command reads the name the component was found by, a region
        view.view.substr = lambda at: source[at] if isinstance(at, int) else receiver
        return di.get_property_name(view, variable_names.find_cfc(view))

    # jwt is a property already, and its bean is not a property to add
    assert property_name('jwt.encode()', metadata) is None
    # a name that is not a property is the property to add
    assert property_name('userService.getUser()', NO_PROPERTIES) == 'UserService'


@pytest.mark.parametrize('receiver', ['users', 'lazyUsers', 'userService'])
def test_the_prefixes_of_an_inject_attribute_and_a_bare_one(wirebox, main, receiver):
    project_name, file_path, metadata = main

    view = call_view(project_name, receiver, 'getuser', file_path, metadata)
    reference = variable_names.find_call_cfc(view)
    assert reference is not None
    assert reference.file_path == (wirebox / 'models' / 'UserService.cfc').as_posix()


def test_the_bean_comes_before_the_variable_name(wirebox, main):
    project_name, file_path, metadata = main
    user_service = (wirebox / 'models' / 'UserService.cfc').as_posix()
    mail = (wirebox / 'services' / 'Mail.cfc').as_posix()

    # mail is injected as UserService, and also the name of Mail
    view = call_view(project_name, 'mail', 'missing', file_path, metadata)
    reference = variable_names.find_call_cfc(view)
    assert reference is not None
    assert (reference.file_path, reference.candidates) == (user_service, (mail,))

    # the one that has the method
    view = call_view(project_name, 'mail', 'send', file_path, metadata)
    reference = variable_names.find_call_cfc(view)
    assert reference is not None
    assert (reference.file_path, reference.candidates) == (mail, ())

    view = dot_view(project_name, 'mail', file_path, metadata)
    assert items(variable_names.get_dot_completions(view)) == [
        ('getUser', 'models/UserService'),
        ('send', 'services/Mail'),
    ]


def test_the_declaration_of_an_injected_property_is_its_bean(wirebox, main):
    project_name, file_path, metadata = main
    name_region = Region(14, 17)
    view = types.SimpleNamespace(
        match_selector=lambda pt, selector: selector == 'meta.tag.property.name.cfml',
        word=lambda pt: name_region,
        substr=lambda region: 'jwt',
    )
    cfml_view = types.SimpleNamespace(
        view=view,
        project_name=project_name,
        file_path=file_path,
        position=15,
        view_metadata=metadata,
    )

    reference = variable_names.find_cfc(cfml_view)
    assert reference is not None
    assert reference.class_name == 'JWTService'
    assert reference.regions == [name_region]


def test_what_a_method_of_a_bean_returns_is_no_component(wirebox, main):
    project_name, file_path, metadata = main
    metadata['properties']['mail']['meta']['inject'] = 'model:userService:getMailer'

    # not the components of the bean or of the name
    view = call_view(project_name, 'mail', 'send', file_path, metadata)
    assert variable_names.find_call_cfc(view) is None


def test_a_configured_project_finds_the_bean_by_its_names(tmp_path, project, names):
    write(
        tmp_path / 'models' / 'UserService.cfc', 'component { function getUser() {} }'
    )
    write(
        tmp_path / 'handlers' / 'Main.cfc',
        'component {\n    property name="users" inject="id:UserService";\n}',
    )
    project_name = project(
        {'cfc_folders': [{'path': 'models', 'variable_names': ['{cfc}']}]}
    )
    names.reindex_project(project_name)
    file_path = (tmp_path / 'handlers' / 'Main.cfc').as_posix()
    metadata = view_metadata(names, project_name, file_path)

    view = call_view(project_name, 'users', 'getuser', file_path, metadata)
    reference = variable_names.find_call_cfc(view)
    assert reference is not None
    assert reference.file_path == (tmp_path / 'models' / 'UserService.cfc').as_posix()
    # a name that the project file gives is not a guess
    assert reference.guessed is False


@pytest.fixture
def coldbox(tmp_path, git_environment, index, names):
    """
    A ColdBox app with ColdBox installed into the ignored lib folder, a
    handler named Log, and a handler with framework objects injected. Returns
    the project, the folder, and a view of the handler.
    """
    site = git_repo(tmp_path / 'site')
    write(site / '.gitignore', 'lib/\n')
    write(site / 'box.json', json.dumps({'installPaths': {'coldbox': 'lib/coldbox'}}))
    system = site / 'lib' / 'coldbox' / 'system'
    write(
        system / 'logging' / 'Logger.cfc',
        'component accessors="true" {\n'
        '    property name="category";\n'
        '    function info(message) {}\n'
        '}',
    )
    write(system / 'web' / 'Controller.cfc', 'component { function getSetting() {} }')
    write(system / 'ioc' / 'Injector.cfc', 'component { function getInstance() {} }')
    write(site / 'handlers' / 'Log.cfc', 'component { function index() {} }')
    # the app's router extends the framework's, which is not installed here
    write(site / 'config' / 'Router.cfc', 'component { function configure() {} }')
    write(
        site / 'handlers' / 'Main.cfc',
        'component {\n'
        '    property name="log" inject="logbox:logger:{this}";\n'
        '    property name="logHandler" inject="coldbox:setting:x";\n'
        '    property name="main" inject="coldbox:renderer";\n'
        '    property name="router" inject="coldbox:router";\n'
        '    property name="controller" inject="coldbox";\n'
        '    property name="injector" inject="wirebox";\n'
        '}',
    )
    project_name = add_project([site])
    file_path = (site / 'handlers' / 'Main.cfc').as_posix()
    return project_name, site, view_metadata(names, project_name, file_path)


def test_a_framework_dsl_is_its_class_and_not_the_name(coldbox):
    project_name, site, metadata = coldbox
    logger = (site / 'lib' / 'coldbox' / 'system' / 'logging' / 'Logger.cfc').as_posix()

    # the name finds the handler
    assert paths(cfcs.lookup(project_name, ['log']), site) == ['handlers/Log.cfc']

    view = dot_view(project_name, 'log', metadata=metadata)
    assert items(variable_names.get_dot_completions(view)) == [
        ('getCategory', 'any'),
        ('info', ''),
        ('setCategory', 'void'),
    ]
    view.dot_context.append(Symbol('variables', False, None, None, Region(0, 9)))
    assert items(variable_names.get_dot_completions(view)) == [
        ('getCategory', 'any'),
        ('info', ''),
        ('setCategory', 'void'),
    ]

    # hover and goto
    reference = variable_names.find_cfc(
        method_view(project_name, 'log.info()', metadata=metadata)
    )
    assert reference is not None
    assert (reference.file_path, reference.class_name) == (logger, 'Logger')
    assert reference.function_name == 'info'

    # the parameter popup; a class known by its dot path is not a guess
    view = call_view(project_name, 'log', 'info', metadata=metadata)
    name_region = view.function_call_params.dot_context[0].name_region
    assert variable_names.find_call_cfc(view) == ComponentReference(
        logger, 'Logger', None, [name_region], guessed=False
    )


@pytest.mark.parametrize(
    ('receiver', 'function_name', 'class_path'),
    [
        ('controller', 'getsetting', 'web/Controller.cfc'),
        ('injector', 'getinstance', 'ioc/Injector.cfc'),
    ],
)
def test_the_coldbox_and_wirebox_dsls(coldbox, receiver, function_name, class_path):
    project_name, site, metadata = coldbox

    view = call_view(project_name, receiver, function_name, metadata=metadata)
    reference = variable_names.find_call_cfc(view)
    assert reference is not None
    assert (
        reference.file_path
        == (site / 'lib' / 'coldbox' / 'system' / class_path).as_posix()
    )


@pytest.mark.parametrize(
    ('receiver', 'name_finds'),
    [
        # a DSL that the table does not have
        ('logHandler', 'handlers/Log.cfc'),
        # a DSL whose class is not in the index
        ('main', 'handlers/Main.cfc'),
        # a class that only a file of the same name could be
        ('router', 'config/Router.cfc'),
    ],
)
def test_a_framework_dsl_without_a_class_is_no_component(coldbox, receiver, name_finds):
    project_name, site, metadata = coldbox

    found = paths(cfcs.lookup(project_name, [receiver]), site)
    assert found == ([name_finds] if name_finds else [])
    assert (
        paths(
            cfcs.lookup_class(project_name, 'coldbox.system.web.routing.Router'), site
        )
        == []
    )

    view = dot_view(project_name, receiver, metadata=metadata)
    assert variable_names.get_dot_completions(view) is None
    view = call_view(project_name, receiver, 'index', metadata=metadata)
    assert variable_names.find_call_cfc(view) is None
    source = receiver + '.index()'
    assert (
        variable_names.find_cfc(method_view(project_name, source, metadata=metadata))
        is None
    )
