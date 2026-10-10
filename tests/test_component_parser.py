import sqlite3

from CFML.src import minihtml
from CFML.src.component_index import completions
from component_parser import Parser, parse_cfc_file_string

SCRIPT_COMPONENT = """/**
 * A user service
 * @author Someone
 */
component extends="models.BaseService" accessors="true" persistent="true" entityname="AppUser" {
    property name="name" type="string";
    property name="age" type="numeric" setter="false";
    property string nickname;

    /**
     * Finds a user
     * @id The user id
     */
    public models.User function find(required numeric id, string status = "active", struct opts = {a: 1}) {
        // function notThis() {}
        var s = "function alsoNot() {}";
        return entityLoadByPK("User", arguments.id);
    }

    private void function helper() output="false" {
        property = 1;
    }
}
"""

TAG_COMPONENT = """<cfcomponent extends="models.Base" accessors="true" output="false" hint="Tag based">
    <cfproperty name="title" type="string">
    <cffunction name="save" access="public" returntype="boolean" hint="Saves it">
        <cfargument name="force" type="boolean" required="true" hint="Overwrite">
        <cfargument name="note" default="">
        <cfreturn true>
    </cffunction>
    <!--- <cffunction name="commentedOut"></cffunction> --->
</cfcomponent>
"""


def test_script_component_attributes_and_docblock():
    meta = parse_cfc_file_string(SCRIPT_COMPONENT)
    assert meta['extends'] == 'models.BaseService'
    assert meta['accessors'] is True
    assert meta['persistent'] is True
    assert meta['entityname'] == 'AppUser'
    assert meta['initmethod'] is None
    assert meta['hint'] == 'A user service'
    assert meta['author'] == 'Someone'


def test_docblock_before_component_modifiers():
    meta = parse_cfc_file_string(
        '/**\n'
        ' * An abstract base\n'
        ' * @author Someone\n'
        ' */\n'
        'abstract component extends="Base" {\n'
        '}'
    )
    assert meta['hint'] == 'An abstract base'
    assert meta['author'] == 'Someone'
    assert meta['extends'] == 'Base'
    assert 'abstract' not in meta

    meta = parse_cfc_file_string(
        '/**\n * A final one\n */\nFINAL component accessors="true" {\n}'
    )
    assert meta['hint'] == 'A final one'
    assert meta['accessors'] is True


def test_component_declaration_is_not_the_word_in_a_comment():
    meta = parse_cfc_file_string(
        '// this component handles users\n'
        '/* A component for users { } */\n'
        'component extends="Base" accessors=true {\n'
        '    variables.name = "a component";\n'
        '}'
    )
    assert meta['extends'] == 'Base'
    assert meta['accessors'] is True
    assert 'handles' not in meta
    assert 'for' not in meta

    meta = parse_cfc_file_string(
        '<!--- <cfcomponent extends="Old"> --->\n'
        '<cfcomponent extends="Base">\n'
        '</cfcomponent>'
    )
    assert meta['extends'] == 'Base'

    meta = parse_cfc_file_string('// not a component\nfunction f() {}')
    assert meta['extends'] is None
    assert 'not' not in meta
    assert set(meta['functions']) == {'f'}


def test_argument_snippets_escape_snippet_characters():
    parameters = parse_cfc_file_string(
        '<cfcomponent>\n'
        '<cffunction name="f">\n'
        '    <cfargument name="$id" required="true">\n'
        '    <cfargument name="opts" type="struct" default="#{a: {b: 1}}#">\n'
        '    <cfargument name="pattern" default="\\d+">\n'
        '</cffunction>\n'
        '</cfcomponent>'
    )['functions']['f']['meta']['parameters']
    assert completions.make_arguments_string(parameters, 'full') == (
        '${1:required \\$id}'
        '${2:, ${3:struct opts={a: {b: 1\\}\\}}}'
        '${4:, ${5:pattern=\\\\d+}}'
    )
    assert completions.make_arguments_string(parameters, 'required') == '${1:\\$id}'
    # plain arguments are unchanged
    plain = [{'name': 'id', 'required': True, 'type': 'numeric', 'default': None}]
    assert completions.make_arguments_string(plain, 'full') == (
        '${1:required numeric id}'
    )


def test_script_functions_skip_comments_and_strings():
    functions = parse_cfc_file_string(SCRIPT_COMPONENT)['functions']
    explicit = {key for key, funct in functions.items() if not funct['implicit']}
    assert explicit == {'find', 'helper'}


def test_script_function_signature():
    find = parse_cfc_file_string(SCRIPT_COMPONENT)['functions']['find']
    assert find['name'] == 'find'
    assert find['meta']['access'] == 'public'
    assert find['meta']['returntype'] == 'models.User'
    assert find['meta']['hint'] == 'Finds a user'
    id_param, status_param, opts_param = find['meta']['parameters']
    assert id_param['name'] == 'id'
    assert id_param['required'] is True
    assert id_param['type'] == 'numeric'
    assert id_param['hint'] == 'The user id'
    assert status_param['default'] == '"active"'
    assert status_param['required'] is False
    assert opts_param['default'] == '{a: 1}'


def script_function_meta(source):
    functions = parse_cfc_file_string('component {\n    ' + source + '\n}')['functions']
    return {key: funct['meta'] for key, funct in functions.items()}


def parameter_fields(meta):
    return [
        (param['required'], param['type'], param['name'], param['default'])
        for param in meta['parameters']
    ]


def test_script_function_array_types():
    meta = script_function_meta(
        'public string[] function names(required string[] names) {}\n'
        '    models.User[] function users(models.User[] users, Foo[] b = []) {}\n'
        '    STRING[] function upper() {}'
    )
    assert meta['names']['returntype'] == 'string[]'
    assert meta['names']['access'] == 'public'
    assert parameter_fields(meta['names']) == [(True, 'string[]', 'names', None)]
    assert meta['users']['returntype'] == 'models.User[]'
    assert parameter_fields(meta['users']) == [
        (False, 'models.User[]', 'users', None),
        (False, 'Foo[]', 'b', '[]'),
    ]
    assert meta['upper']['returntype'] == 'STRING[]'


def test_script_function_types_without_brackets():
    meta = script_function_meta(
        'private models.User function find(\n'
        '        required string name = "x",\n'
        '        models.User user,\n'
        '        array list = [1, 2],\n'
        '        plain\n'
        '    ) {}'
    )
    assert meta['find']['returntype'] == 'models.User'
    assert meta['find']['access'] == 'private'
    assert parameter_fields(meta['find']) == [
        (True, 'string', 'name', '"x"'),
        (False, 'models.User', 'user', None),
        (False, 'array', 'list', '[1, 2]'),
        (False, None, 'plain', None),
    ]


def test_script_function_parameters_with_comments_between_them():
    meta = script_function_meta(
        'function f(required string a, /* note, with a comma */ numeric b, // trailing, too\n'
        '        c /** the c */) {}'
    )
    assert parameter_fields(meta['f']) == [
        (True, 'string', 'a', None),
        (False, 'numeric', 'b', None),
        (False, None, 'c', None),
    ]
    # no attributes are read from the comments
    assert [set(param) for param in meta['f']['parameters']] == [
        {'name', 'required', 'type', 'default'}
    ] * 3


def test_dollar_signs_in_names_and_types():
    meta = parse_cfc_file_string(
        'component accessors="true" {\n'
        '    property name="my$prop";\n'
        '    property string $short;\n'
        '    property my$type $typed;\n'
        '    my$Type function $get$(required my$type $v, $w = $x, string[] $list) {\n'
        '        var $x = 1;\n'
        '    }\n'
        '}'
    )
    assert {key: prop['meta']['type'] for key, prop in meta['properties'].items()} == {
        'my$prop': 'any',
        '$short': 'string',
        '$typed': 'my$type',
    }
    assert meta['properties']['$short']['name'] == '$short'
    assert meta['properties']['$short']['meta'] == {
        'type': 'string',
        'getter': None,
        'setter': None,
    }
    assert {'get$short', 'set$typed'} <= set(meta['functions'])
    function = meta['functions']['$get$']
    assert function['name'] == '$get$'
    assert function['meta']['returntype'] == 'my$Type'
    assert parameter_fields(function['meta']) == [
        (True, 'my$type', '$v', None),
        (False, None, '$w', '$x'),
        (False, 'string[]', '$list', None),
    ]


def test_script_parameter_default_with_nested_brackets():
    meta = script_function_meta(
        'function f(\n'
        '        struct options = { a: { b: 1 }, c: [1, 2] } hint="the options",\n'
        '        array rows = [[1], [2]],\n'
        '        numeric n = (1 + (2)),\n'
        '        struct quoted = {k: "}"},\n'
        '        last = foo(bar(1))\n'
        '    ) {}'
    )
    assert parameter_fields(meta['f']) == [
        (False, 'struct', 'options', '{ a: { b: 1 }, c: [1, 2] }'),
        (False, 'array', 'rows', '[[1], [2]]'),
        (False, 'numeric', 'n', '(1 + (2))'),
        (False, 'struct', 'quoted', '{k: "}"}'),
        (False, None, 'last', 'foo(bar(1))'),
    ]
    assert meta['f']['parameters'][0]['hint'] == 'the options'
    assert set(meta['f']['parameters'][0]) == {
        'name',
        'required',
        'type',
        'default',
        'hint',
    }


def test_script_function_attributes():
    helper = parse_cfc_file_string(SCRIPT_COMPONENT)['functions']['helper']
    assert helper['meta']['access'] == 'private'
    assert helper['meta']['returntype'] == 'void'
    assert helper['meta']['output'] == 'false'


def test_script_function_modifiers_around_the_return_type():
    functions = parse_cfc_file_string(
        'component {\n'
        '    boolean private function hidden() {}\n'
        '    com.foo.Bar private static function make() {}\n'
        '    static public struct function two() {}\n'
        '    final public string function three() {}\n'
        '    private static final numeric function four() {}\n'
        '    public static string final function five() {}\n'
        '    PUBLIC STATIC STRING FUNCTION six() {}\n'
        '    static function seven() {}\n'
        '    any function eight() {}\n'
        '    function nine() {}\n'
        '}'
    )['functions']
    signatures = {
        key: (
            funct['meta']['access'],
            funct['meta'].get('modifier'),
            funct['meta']['returntype'],
        )
        for key, funct in functions.items()
    }
    assert signatures == {
        'hidden': ('private', None, 'boolean'),
        'make': ('private', 'static', 'com.foo.Bar'),
        'two': ('public', 'static', 'struct'),
        'three': ('public', 'final', 'string'),
        # with more than one storage modifier the last is kept
        'four': ('private', 'final', 'numeric'),
        'five': ('public', 'final', 'string'),
        'six': ('PUBLIC', 'STATIC', 'STRING'),
        'seven': ('public', 'static', None),
        'eight': ('public', None, 'any'),
        'nine': ('public', None, None),
    }


def test_script_function_return_type_is_not_taken_from_the_line_above():
    meta = script_function_meta(
        '// returns the user\n'
        '    function getUser() {}\n'
        '    // a private\n'
        '    public function helper() {}\n'
        '    variables.x = 1\n'
        '    function afterStatement() {}\n'
        '    /* the first\n'
        '       of the static */\n'
        '    // helpers\n'
        '    string function afterComments() {}'
    )
    signatures = {
        key: (funct['access'], funct.get('modifier'), funct['returntype'])
        for key, funct in meta.items()
    }
    assert signatures == {
        'getuser': ('public', None, None),
        'helper': ('public', None, None),
        'afterstatement': ('public', None, None),
        'aftercomments': ('public', None, 'string'),
    }


def test_script_function_is_indexed_with_its_return_type_on_the_line_above():
    # the modifiers and return type are only read from the function's line
    meta = script_function_meta(
        'private string\n'
        '    function split() {}\n'
        '    private\n'
        '    string function half() {}\n'
        '    private\tstring\tfunction tabs() {}'
    )
    signatures = {
        key: (funct['access'], funct['returntype']) for key, funct in meta.items()
    }
    assert signatures == {
        'split': ('public', None),
        'half': ('public', 'string'),
        'tabs': ('private', 'string'),
    }


def test_script_function_name_is_not_taken_from_the_line_below():
    # a comment that ends in the word function, above a statement
    meta = script_function_meta(
        'function first() {\n'
        '        // exit the function\n'
        '        if ( done ) return;\n'
        '        // iterate over the values of the function\n'
        '        for( key in values ){}\n'
        '    }\n'
        '    private function\tlast() {}\n'
        '    dysfunction notThis() {}'
    )
    assert set(meta) == {'first', 'last'}
    assert meta['last']['access'] == 'private'


def test_script_function_docblock_is_on_the_lines_above():
    meta = script_function_meta(
        '/**\n'
        '     * Finds a user\n'
        '     */\n'
        '\n'
        '    private models.User function find() {}\n'
        '    /** Counts them */ public numeric function count() {}\n'
        '    /**\n'
        '     * Not the hint of the function below\n'
        '     */\n'
        '    // a comment\n'
        '    function plain() {}'
    )
    assert meta['find']['hint'] == 'Finds a user'
    assert meta['find']['access'] == 'private'
    assert meta['find']['returntype'] == 'models.User'
    assert meta['count']['returntype'] == 'numeric'
    assert meta['plain']['returntype'] is None
    assert 'hint' not in meta['plain']


def test_single_line_docblocks():
    meta = parse_cfc_file_string(
        '/** A user service */\n'
        'component {\n'
        '    /** Returns the thing */ function get() {}\n'
        '    /** Finds one @id.hint is not a tag here */\n'
        '    function find(id) {}\n'
        '    /** @id.hint the key */\n'
        '    function load(id) {}\n'
        '}'
    )
    assert meta['hint'] == 'A user service'
    functions = {key: funct['meta'] for key, funct in meta['functions'].items()}
    assert functions['get']['hint'] == 'Returns the thing'
    assert functions['find']['hint'] == 'Finds one @id.hint is not a tag here'
    assert 'hint' not in functions['find']['parameters'][0]
    assert 'hint' not in functions['load']
    assert functions['load']['parameters'][0]['hint'] == 'the key'


def test_banner_comment_is_not_a_docblock():
    meta = script_function_meta(
        '/*********************************** BDD SUITES ***********************************/\n'
        '    function run() {}\n'
        '    /*** not a doc comment ***/ function other() {}\n'
        '    /** Still a doc comment */ function last() {}'
    )
    assert 'hint' not in meta['run']
    assert 'hint' not in meta['other']
    assert meta['last']['hint'] == 'Still a doc comment'

    meta = parse_cfc_file_string(
        '/**************** A banner ****************/\ncomponent {}'
    )
    assert 'hint' not in meta


def test_docblock_with_blank_lines():
    meta = script_function_meta(
        '/**\n'
        '     * Finds a user\n'
        '     *\n'
        '     * by the key\n'
        '     *\n'
        '     * @id the key\n'
        '     * @deprecated\n'
        '     * @return the user\n'
        '     */\n'
        '    function find(id) {}'
    )
    assert meta['find']['hint'] == 'Finds a user\nby the key'
    assert meta['find']['parameters'][0]['hint'] == 'the key'
    assert meta['find']['deprecated'] == ''
    assert meta['find']['return'] == 'the user'


def test_tags_without_text_set_no_hint():
    meta = script_function_meta(
        '/**\n'
        '     * Obtains an instance of Duration from another duration\n'
        '     *\n'
        '     * @amount\n'
        '     * @param unit\n'
        '     * @other.hint\n'
        '     * @deprecated\n'
        '     */\n'
        '    function from( required Duration amount, unit, other ) {}\n'
        '    /**\n'
        '     * The text\n'
        '     * @hint\n'
        '     */\n'
        '    function bare() {}'
    )
    assert (
        meta['from']['hint'] == 'Obtains an instance of Duration from another duration'
    )
    for param in meta['from']['parameters']:
        assert 'hint' not in param
    # a tag that means something without text is kept
    assert meta['from']['deprecated'] == ''
    # an empty @hint does not hide the text above the tags
    assert meta['bare']['hint'] == 'The text'


def test_docblock_tag_text_over_several_lines():
    meta = script_function_meta(
        '/**\n'
        '     * Finds a user\n'
        '     * @id The user id,\n'
        '     *     which is numeric\n'
        '     * @param status The status\n'
        '     *     to look for\n'
        '     * @param other Not a parameter of this function\n'
        '     * @param flag\n'
        '     *     on its own line\n'
        '     * @return the user\n'
        '     *     or null\n'
        '     */\n'
        '    function find(id, status, flag) {}'
    )
    find = meta['find']
    assert find['hint'] == 'Finds a user'
    assert find['parameters'][0]['hint'] == 'The user id,\nwhich is numeric'
    assert find['parameters'][1]['hint'] == 'The status\nto look for'
    assert find['parameters'][2]['hint'] == 'on its own line'
    assert find['return'] == 'the user\nor null'
    # a @param tag for no parameter is kept as before
    assert find['param'] == 'other Not a parameter of this function'

    meta = parse_cfc_file_string(
        '/**\n'
        ' * @hint A user service\n'
        ' *   with a long hint\n'
        ' * @author Someone\n'
        ' */\n'
        'component {}'
    )
    assert meta['hint'] == 'A user service\nwith a long hint'
    assert meta['author'] == 'Someone'


def test_script_properties():
    # an assignment to a variable named property in a function body is
    # not a property declaration
    properties = parse_cfc_file_string(SCRIPT_COMPONENT)['properties']
    assert set(properties) == {'name', 'age', 'nickname'}
    assert properties['name']['meta']['type'] == 'string'
    assert properties['age']['meta']['setter'] is False
    assert properties['nickname']['meta']['type'] == 'string'


def test_script_property_after_a_statement_is_indexed():
    # properties used to be found only after a // comment line
    meta = parse_cfc_file_string(
        'component {\n    property name="first";\n    property name="second";\n}'
    )
    assert set(meta['properties']) == {'first', 'second'}


def test_script_property_at_the_start_of_a_line_after_a_comment():
    # the comment's range ends where the property starts
    meta = parse_cfc_file_string(
        'component {\n'
        '// the name\n'
        'property name="first";\n'
        '// the age\n'
        'property name="second";\n'
        'function f() {\n'
        '// not a property\n'
        'property name="notThis";\n'
        '}\n'
        '}'
    )
    assert set(meta['properties']) == {'first', 'second'}


def test_script_properties_without_semicolons():
    # the first property used to run on to the next semicolon
    meta = parse_cfc_file_string(
        'component accessors="true" {\n'
        '    property name="first" type="string"\n'
        '    property numeric second\n'
        '    property name="third" // it\'s the last\n'
        '\n'
        '    function f( name = "notThis" ) {\n'
        '        return 1;\n'
        '    }\n'
        '}'
    )
    assert {key: prop['meta'] for key, prop in meta['properties'].items()} == {
        'first': {'type': 'string', 'getter': None, 'setter': None},
        'second': {'type': 'numeric', 'getter': None, 'setter': None},
        'third': {'type': 'any', 'getter': None, 'setter': None},
    }
    assert 'getsecond' in meta['functions']


def test_script_property_over_several_lines():
    meta = parse_cfc_file_string(
        'component {\n'
        '    property\n'
        '        name = "first"\n'
        '        type="string"\n'
        '        delegate;\n'
        '    property name="second" inject\n'
        '        lazy;\n'
        '    property name="third"\n'
        '}'
    )
    assert {key: prop['meta'] for key, prop in meta['properties'].items()} == {
        'first': {'type': 'string', 'getter': None, 'setter': None, 'delegate': ''},
        'second': {
            'type': 'any',
            'getter': None,
            'setter': None,
            'inject': '',
            'lazy': '',
        },
        'third': {'type': 'any', 'getter': None, 'setter': None},
    }


def test_property_with_a_dotted_type():
    meta = parse_cfc_file_string(
        'component accessors="true" {\n'
        '    property name="svc" type="models.Service";\n'
        '    property models.Service other;\n'
        '    property com.acme.Repo repo inject="id:repo";\n'
        '}'
    )
    assert {key: prop['meta'] for key, prop in meta['properties'].items()} == {
        'svc': {'type': 'models.Service', 'getter': None, 'setter': None},
        'other': {'type': 'models.Service', 'getter': None, 'setter': None},
        'repo': {
            'type': 'com.acme.Repo',
            'getter': None,
            'setter': None,
            'inject': 'id:repo',
        },
    }
    assert meta['functions']['getother']['meta']['returntype'] == 'models.Service'


def test_property_string_holds_what_ends_a_property():
    meta = parse_cfc_file_string(
        'component {\n'
        '    property name="first" hint="a; b > c\n'
        '        // d" type="string";\n'
        '}'
    )
    assert meta['properties']['first']['meta']['type'] == 'string'
    assert meta['properties']['first']['meta']['hint'] == 'a; b > c\n        // d'

    meta = parse_cfc_file_string(
        '<cfcomponent>\n'
        '<cfproperty name="first" hint="a > b; c" type="string">\n'
        '<cfproperty name="second"\n'
        '    type="numeric" />\n'
        '</cfcomponent>'
    )
    assert meta['properties']['first']['meta']['type'] == 'string'
    assert meta['properties']['second']['meta']['type'] == 'numeric'


def test_property_with_an_empty_name_is_not_a_property():
    # an accessor is named after its property, so this used to raise
    for empty in ['property name="";', "property name='';", 'property name=;']:
        meta = parse_cfc_file_string(
            'component accessors="true" {\n'
            '    property name="first";\n'
            '    ' + empty + '\n'
            '    property name="last" type="string";\n'
            '    function f() {}\n'
            '}'
        )
        assert set(meta['properties']) == {'first', 'last'}
        assert set(meta['functions']) == {
            'getfirst',
            'setfirst',
            'getlast',
            'setlast',
            'f',
        }

    meta = parse_cfc_file_string(
        '<cfcomponent accessors="true">\n'
        '<cfproperty name="">\n'
        '<cfproperty name="title">\n'
        '</cfcomponent>'
    )
    assert set(meta['properties']) == {'title'}
    assert set(meta['functions']) == {'gettitle', 'settitle'}


DESTRUCTURING_COMPONENT = """component {
    /**
     * @d The d
     */
    function f({a, b: {c}} = {}, d) {}
    function g(
        {
            a,
            b: { c },
            "k}": [ m ],
            ...r
        } = {},
        struct opts = {x: 1},
        required string name hint="n"
    ) {}
    function h({ k, v = {} }, [first, second]) {}
}
"""


def destructuring_parameters(function_name):
    functions = parse_cfc_file_string(DESTRUCTURING_COMPONENT)['functions']
    return functions[function_name]['meta']['parameters']


def test_destructured_parameter_is_one_parameter():
    pattern, d = destructuring_parameters('f')
    assert pattern == {
        'name': '{a, b: {c}}',
        'required': False,
        'type': None,
        'default': '{}',
        'destructuring': True,
    }
    assert d == {
        'name': 'd',
        'required': False,
        'type': None,
        'default': None,
        'hint': 'The d',
    }


def test_destructured_parameter_name_is_its_source_text():
    pattern, opts, name = destructuring_parameters('g')
    # whitespace collapsed; the brace in a string does not end the pattern
    assert pattern['name'] == '{ a, b: { c }, "k}": [ m ], ...r }'
    assert pattern['default'] == '{}'
    assert pattern['destructuring'] is True
    # a struct default does not make a pattern
    assert opts['name'] == 'opts'
    assert opts['type'] == 'struct'
    assert opts['default'] == '{x: 1}'
    assert 'destructuring' not in opts
    assert name['name'] == 'name'
    assert name['required'] is True
    assert name['type'] == 'string'
    assert name['hint'] == 'n'


def test_destructured_parameter_without_a_default():
    struct_pattern, array_pattern = destructuring_parameters('h')
    assert struct_pattern['name'] == '{ k, v = {} }'
    assert struct_pattern['default'] is None
    # the grammar takes only a struct pattern here, but an array pattern
    # is no more a parameter name
    assert array_pattern['name'] == '[first, second]'
    assert array_pattern['destructuring'] is True


def test_rest_parameters():
    # the form of ColdFusion 2021 and later: `...name`, with no type
    meta = script_function_meta(
        'function f(...names) {}\n'
        '    function g(a, b, ...manyMoreArgs) {}\n'
        '    function h(required numeric a, ...users hint="the users") {}'
    )
    assert meta['f']['parameters'] == [
        {
            'name': 'names',
            'required': False,
            'type': None,
            'default': None,
            'rest': True,
        }
    ]
    a, b, many = meta['g']['parameters']
    assert 'rest' not in a and 'rest' not in b
    assert many == {
        'name': 'manyMoreArgs',
        'required': False,
        'type': None,
        'default': None,
        'rest': True,
    }
    a, users = meta['h']['parameters']
    assert 'rest' not in a
    assert users == {
        'name': 'users',
        'required': False,
        'type': None,
        'default': None,
        'hint': 'the users',
        'rest': True,
    }
    # completions write a rest parameter as the signature does
    assert completions.make_arguments_string(meta['h']['parameters'], 'full') == (
        '${1:required numeric a}${2:, ${3:...users}}'
    )
    assert (
        completions.make_arguments_string(meta['f']['parameters'], 'full')
        == '${1:...names}'
    )
    assert (
        completions.make_arguments_string(meta['f']['parameters'], 'required')
        == '${1:...names}'
    )


def test_implicit_accessors():
    functions = parse_cfc_file_string(SCRIPT_COMPONENT)['functions']
    assert functions['getname']['implicit'] is True
    assert functions['getname']['name'] == 'getName'
    assert functions['getname']['meta']['returntype'] == 'string'
    assert functions['setname']['meta']['parameters'][0]['name'] == 'name'
    assert 'getage' in functions
    # setter="false" on the property
    assert 'setage' not in functions


def test_parameter_doc_header_escapes_the_name_and_type():
    header = minihtml.param_header(
        {'name': '{a = x & "<b>"}', 'type': 'Foo<T>', 'required': True}
    )
    assert '{a = x &amp; "&lt;b&gt;"}' in header
    assert 'Foo&lt;T&gt;' in header
    assert '<b>' not in header
    # plain names and types are unchanged
    header = minihtml.param_header({'name': 'id', 'type': 'models.User[]'})
    assert header.strip() == (
        '<strong>id: <span class="storage-type">models.User[]</span></strong>'
    )


def test_no_accessors_without_the_accessors_attribute():
    meta = parse_cfc_file_string('component {\n    property name="first";\n}')
    assert meta['accessors'] is False
    assert set(meta['properties']) == {'first'}
    assert 'getfirst' not in meta['functions']


def test_tag_component():
    meta = parse_cfc_file_string(TAG_COMPONENT)
    assert meta['extends'] == 'models.Base'
    assert meta['hint'] == 'Tag based'
    assert set(meta['properties']) == {'title'}
    explicit = {
        key for key, funct in meta['functions'].items() if not funct['implicit']
    }
    assert explicit == {'save'}
    assert {'gettitle', 'settitle'} <= set(meta['functions'])


def test_tag_properties_in_any_case():
    meta = parse_cfc_file_string(
        '<cfcomponent>\n'
        '<CFPROPERTY name="flush">\n'
        '    <CFPROPERTY name="indented" type="numeric">\n'
        '    <CfProperty name="mixed">\n'
        '    <cfproperty name="lower">\n'
        '</cfcomponent>'
    )
    assert set(meta['properties']) == {'flush', 'indented', 'mixed', 'lower'}
    assert meta['properties']['indented']['meta']['type'] == 'numeric'


def test_script_properties_in_any_case():
    meta = parse_cfc_file_string(
        'component {\n'
        '    PROPERTY name="first";\n'
        '    function f() {\n'
        '        property name="notThis";\n'
        '    }\n'
        '}'
    )
    assert set(meta['properties']) == {'first'}


def test_tag_function_signature():
    save = parse_cfc_file_string(TAG_COMPONENT)['functions']['save']
    assert save['meta']['access'] == 'public'
    assert save['meta']['returntype'] == 'boolean'
    assert save['meta']['hint'] == 'Saves it'
    force, note = save['meta']['parameters']
    assert force['name'] == 'force'
    assert force['required'] is True
    assert force['type'] == 'boolean'
    assert force['hint'] == 'Overwrite'
    assert note['name'] == 'note'
    assert note['required'] is False
    assert note['default'] == ''
    # the tag name is not an attribute
    assert set(force) == {'name', 'type', 'required', 'hint', 'default'}
    assert set(note) == {'name', 'type', 'required', 'default'}


def test_tag_attributes_with_a_greater_than_sign_in_quotes():
    meta = parse_cfc_file_string(
        '<cfcomponent hint="a > b" extends="Base">\n'
        '<cffunction name="f" hint="a > b" returntype="string">\n'
        '    <cfargument name="x" default="x > 1" type="numeric">\n'
        "    <cfargument name='y' hint='y > x' required='true'>\n"
        '</cffunction>\n'
        '</cfcomponent>'
    )
    assert meta['hint'] == 'a > b'
    assert meta['extends'] == 'Base'
    f = meta['functions']['f']['meta']
    assert f['hint'] == 'a > b'
    assert f['returntype'] == 'string'
    x, y = f['parameters']
    assert (x['name'], x['default'], x['type']) == ('x', 'x > 1', 'numeric')
    assert (y['name'], y['hint'], y['required']) == ('y', 'y > x', True)


def test_tag_function_end_tag_with_whitespace():
    meta = parse_cfc_file_string(
        '<cfcomponent>\n'
        '<cffunction name="a">\n'
        '    <cfargument name="x">\n'
        '</cffunction >\n'
        '<cffunction name="b">\n'
        '    <cfargument name="y">\n'
        '</CFFUNCTION\n>\n'
        '<cffunction name="c">\n'
        '    <cfargument name="z">\n'
        '</cffunction>\n'
        '</cfcomponent>'
    )
    functions = meta['functions']
    assert set(functions) == {'a', 'b', 'c'}
    # each function ends at its own end tag
    assert [p['name'] for p in functions['a']['meta']['parameters']] == ['x']
    assert [p['name'] for p in functions['b']['meta']['parameters']] == ['y']
    assert [p['name'] for p in functions['c']['meta']['parameters']] == ['z']


def test_tag_functions_after_an_apostrophe_in_text():
    # the text between tags is not script, so the apostrophe opens no string
    meta = parse_cfc_file_string(
        '<cfcomponent>\n'
        '<cffunction name="a"><cfmail>Don\'t reply</cfmail></cffunction>\n'
        '<cffunction name="b">\n'
        '    <cfargument name="x">\n'
        '</cffunction>\n'
        '<cffunction name="c"><cfset x = \'y\'></cffunction>\n'
        '<cffunction name="d"></cffunction>\n'
        '<cfproperty name="title">\n'
        '</cfcomponent>'
    )
    functions = meta['functions']
    assert set(functions) == {'a', 'b', 'c', 'd'}
    assert [p['name'] for p in functions['b']['meta']['parameters']] == ['x']
    assert set(meta['properties']) == {'title'}


def test_tag_functions_after_script_comment_markers_in_text():
    meta = parse_cfc_file_string(
        '<cfcomponent>\n'
        '<cffunction name="a">\n'
        '    <cfargument name="x">\n'
        '    <cfoutput>see http://example.com</cfoutput></cffunction>\n'
        '<cffunction name="b">\n'
        '    <cfoutput>/* and "</cfoutput>\n'
        '    <cfargument name="y">\n'
        '</cffunction>\n'
        '<cfproperty name="title">\n'
        '<cffunction name="c"></cffunction>\n'
        '</cfcomponent>'
    )
    functions = meta['functions']
    assert set(functions) == {'a', 'b', 'c'}
    assert [p['name'] for p in functions['a']['meta']['parameters']] == ['x']
    assert [p['name'] for p in functions['b']['meta']['parameters']] == ['y']
    assert set(meta['properties']) == {'title'}


def test_tags_in_the_strings_of_script_are_not_indexed():
    # code that writes a component, in a cfscript block and in a script
    # component; the text of a tag component is still not script
    meta = parse_cfc_file_string(
        '<cfcomponent>\n'
        '<cffunction name="a"><cfmail>Don\'t reply</cfmail></cffunction>\n'
        '<cffunction name="b">\n'
        '    <CFSCRIPT>\n'
        '    out.append( "<cffunction name=""written"">" );\n'
        '    out.append( "<cfargument" );\n'
        '    // <cfargument name="commented">\n'
        "    out.append( '</cffunction>' );\n"
        '    </cfscript>\n'
        '    <cfargument name="x">\n'
        '</cffunction>\n'
        '<cffunction name="c"><cfset x = \'y\'></cffunction>\n'
        '</cfcomponent>'
    )
    functions = meta['functions']
    assert set(functions) == {'a', 'b', 'c'}
    assert [p['name'] for p in functions['b']['meta']['parameters']] == ['x']

    meta = parse_cfc_file_string(
        'component {\n'
        '    function write() {\n'
        '        out.append( "<cffunction name=""written""></cffunction>" );\n'
        '        out.append( "<cfproperty name=""written"">" );\n'
        '    }\n'
        '}'
    )
    assert set(meta['functions']) == {'write'}
    assert meta['properties'] == {}


def test_tag_comments_hide_tags():
    meta = parse_cfc_file_string(
        '<cfcomponent>\n'
        '<!---\n'
        '<cfproperty name="oldTitle">\n'
        '--->\n'
        '<cfproperty name="title">\n'
        '<cffunction name="a">\n'
        '    <!--- <cfargument name="old"> --->\n'
        '    <cfargument name="x">\n'
        '    <!--- </cffunction> --->\n'
        '    <cfargument name="y">\n'
        '</cffunction>\n'
        '<!---\n'
        '<cffunction name="b"></cffunction>\n'
        '--->\n'
        '<cffunction name="c"></cffunction>\n'
        '</cfcomponent>'
    )
    functions = meta['functions']
    assert set(functions) == {'a', 'c'}
    assert [p['name'] for p in functions['a']['meta']['parameters']] == ['x', 'y']
    assert set(meta['properties']) == {'title'}


def test_script_property_in_a_comment_or_string_is_not_indexed():
    meta = parse_cfc_file_string(
        'component {\n'
        '    /*\n'
        '    property name="commented";\n'
        '    */\n'
        '    variables.sql = "\n'
        "    property name='quoted';\n"
        '    ";\n'
        '    property name="first";\n'
        '}'
    )
    assert set(meta['properties']) == {'first'}


def write_components(root):
    (root / 'models').mkdir(parents=True)
    (root / 'models' / 'User.cfc').write_text(SCRIPT_COMPONENT, encoding='utf-8')
    (root / 'Base.cfc').write_text(TAG_COMPONENT, encoding='utf-8')
    (root / 'notes.txt').write_text('not a component', encoding='utf-8')


def test_parse_directory(tmp_path):
    write_components(tmp_path / 'src')
    parser = Parser(str(tmp_path / 'cache.sqlite'))
    index = parser.parse_directory(str(tmp_path / 'src'))
    paths = {path.replace('\\', '/').split('/src/')[1] for path in index}
    assert paths == {'Base.cfc', 'models/User.cfc'}


def test_parse_directory_reuses_the_cache(tmp_path, monkeypatch):
    write_components(tmp_path / 'src')
    cache_path = str(tmp_path / 'cache.sqlite')
    first = Parser(cache_path).parse_directory(str(tmp_path / 'src'))

    import component_parser.cfml_components as cfml_components

    def fail(file_string):
        raise AssertionError('parsed a cached file')

    monkeypatch.setattr(cfml_components, 'parse_cfc_file_string', fail)
    second = Parser(cache_path).parse_directory(str(tmp_path / 'src'))
    assert second == first


def test_a_cleared_cache_has_every_file_parsed_again(tmp_path, monkeypatch):
    write_components(tmp_path / 'src')
    parser = Parser(str(tmp_path / 'cache.sqlite'))
    first = parser.parse_directory(str(tmp_path / 'src'))

    import component_parser.cfml_components as cfml_components

    parsed = []
    parse = cfml_components.parse_cfc_file_string

    def parse_and_count(file_string):
        parsed.append(file_string)
        return parse(file_string)

    monkeypatch.setattr(cfml_components, 'parse_cfc_file_string', parse_and_count)
    parser.clear_cache()
    assert parser.parse_directory(str(tmp_path / 'src')) == first
    assert len(parsed) == 2

    # and they are cached again
    parser.parse_directory(str(tmp_path / 'src'))
    assert len(parsed) == 2


def test_parse_directory_keeps_cached_metadata_a_moved_file_uses(tmp_path, monkeypatch):
    write_components(tmp_path / 'src')
    cache_path = str(tmp_path / 'cache.sqlite')
    parser = Parser(cache_path)
    parser.parse_directory(str(tmp_path / 'src'))

    # a file moved during a session is found in the cache under its new
    # path, and the cache entry outlives its old path at the next start
    (tmp_path / 'src' / 'Base.cfc').rename(tmp_path / 'src' / 'Moved.cfc')
    parser.parse_directory(str(tmp_path / 'src'))

    import component_parser.cfml_components as cfml_components

    def fail(file_string):
        raise AssertionError('parsed a cached file')

    monkeypatch.setattr(cfml_components, 'parse_cfc_file_string', fail)
    index = Parser(cache_path).parse_directory(str(tmp_path / 'src'))
    paths = {path.replace('\\', '/').split('/src/')[1] for path in index}
    assert paths == {'Moved.cfc', 'models/User.cfc'}


def test_parse_file_and_cache_cleanup(tmp_path):
    write_components(tmp_path / 'src')
    cache_path = str(tmp_path / 'cache.sqlite')
    parser = Parser(cache_path)
    parser.parse_directory(str(tmp_path / 'src'))

    user = tmp_path / 'src' / 'models' / 'User.cfc'
    assert set(parser.parse_file(str(user))['properties']) == {
        'name',
        'age',
        'nickname',
    }
    assert parser.parse_file(str(tmp_path / 'src' / 'Missing.cfc')) is None

    # a deleted file's cache entries are removed when a parser starts
    (tmp_path / 'src' / 'Base.cfc').unlink()
    Parser(cache_path)
    con = sqlite3.connect(cache_path)
    paths = [row[0] for row in con.execute('SELECT file_path FROM file_hashes')]
    metadata_rows = con.execute('SELECT COUNT(*) FROM hash_metadata').fetchone()[0]
    con.close()
    assert [path.replace('\\', '/').split('/src/')[1] for path in paths] == [
        'models/User.cfc'
    ]
    assert metadata_rows == 1


def test_a_cache_file_that_is_not_a_database_is_replaced(tmp_path):
    write_components(tmp_path / 'src')
    cache_path = tmp_path / 'cache.sqlite'
    cache_path.write_bytes(b'not a database, but long enough to be read as one' * 40)

    parser = Parser(str(cache_path))
    assert len(parser.parse_directory(str(tmp_path / 'src'))) == 2
    con = sqlite3.connect(cache_path)
    assert con.execute('SELECT COUNT(*) FROM file_hashes').fetchone()[0] == 2
    con.close()


def test_parse_file_returns_none_when_parsing_fails(tmp_path, monkeypatch):
    write_components(tmp_path / 'src')
    import component_parser.cfml_components as cfml_components

    def fail(file_string):
        raise ValueError('unparsable')

    monkeypatch.setattr(cfml_components, 'parse_cfc_file_string', fail)
    parser = Parser(str(tmp_path / 'cache.sqlite'))
    assert parser.parse_file(str(tmp_path / 'src' / 'Base.cfc')) is None


def test_metadata_has_the_keys_its_types_declare():
    from component_parser import metadata as types

    source = """
    /** A user. */
    component accessors="true" {
        property name="name" type="string";
        /** @id.hint the key */
        public numeric function find(required numeric id = 0) {}
    }
    """
    metadata = parse_cfc_file_string(source)

    def has_keys(value, typed_dict):
        assert typed_dict.__required_keys__ <= set(value)
        assert set(value) <= typed_dict.__required_keys__ | typed_dict.__optional_keys__

    has_keys(metadata, types.ComponentMetadata)
    has_keys(metadata['properties']['name'], types.Property)
    has_keys(metadata['properties']['name']['meta'], types.PropertyMeta)
    for name in ['find', 'getname', 'setname']:
        function = metadata['functions'][name]
        has_keys(function, types.Function)
        has_keys(function['meta'], types.FunctionMeta)
        for parameter in function['meta']['parameters']:
            has_keys(parameter, types.Parameter)


def test_parse_files(tmp_path, monkeypatch):
    write_components(tmp_path / 'src')
    user = (tmp_path / 'src' / 'models' / 'User.cfc').as_posix()
    base = (tmp_path / 'src' / 'Base.cfc').as_posix()
    missing = (tmp_path / 'src' / 'Missing.cfc').as_posix()
    cache_path = str(tmp_path / 'cache.sqlite')

    # only the files it is given, and none that cannot be read
    index = Parser(cache_path).parse_files([user, missing])
    assert list(index) == [user]
    assert index == {user: Parser(cache_path).parse_file(user)}

    # and from the cache that parse_directory() fills
    Parser(cache_path).parse_directory(str(tmp_path / 'src'))
    import component_parser.cfml_components as cfml_components

    def fail(file_string):
        raise AssertionError('parsed a cached file')

    monkeypatch.setattr(cfml_components, 'parse_cfc_file_string', fail)
    assert list(Parser(cache_path).parse_files([base, user])) == [base, user]


def test_unquoted_attribute_values_take_any_character_but_a_terminator():
    meta = parse_cfc_file_string(
        'component {\n'
        '    property name=my$prop default=$x;\n'
        '    function f(required string a hint=the$hint, string b default=#now()#) output=false{}\n'
        '    function g() cachedWithin=createTimeSpan(0,1,0,0) {}\n'
        '}'
    )
    assert meta['properties']['my$prop']['meta']['default'] == '$x'
    f = meta['functions']['f']['meta']
    assert f['output'] == 'false'
    assert meta['functions']['g']['meta']['cachedwithin'] == 'createTimeSpan(0,1,0,0)'
    a, b = f['parameters']
    assert a['hint'] == 'the$hint'
    assert b['default'] == '#now()#'
    tag = parse_cfc_file_string(
        '<cfcomponent>\n'
        '<cffunction name=$get returntype=my$type output=false>\n'
        '    <cfargument name=$id default=#now()# />\n'
        '</cffunction>\n'
        '</cfcomponent>'
    )['functions']['$get']['meta']
    assert tag['returntype'] == 'my$type'
    assert tag['parameters'][0]['name'] == '$id'
    # a tag default loses its hashes, as a quoted one does
    assert tag['parameters'][0]['default'] == 'now()'
