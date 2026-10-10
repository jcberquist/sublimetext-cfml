# This module, via index(), takes in a cfml source file string and
# returns a python dict of the function names mapped to a dict
# containing data about the function.

# The structure looks like this:
# {
#   "function_name": {
#     "access": "public/private/etc",
#     "returntype": "any/string/numeric/etc",
#     "parameters": [
#       { "name", "parameter_name"
#         "required": True/False,
#         "type": "any/string/numeric/etc" or None,
#         "default": "defaultvalue" or None,
#         "destructuring": True (only on a destructuring pattern, whose
#                          source text is its name)
#         "rest": True (only on a rest parameter, `...names`)
#       },
#       ...
#     ]
#   },
#   ...
# }

# Known Limitations:
# - attributes are matched on their opening and closing quotes, so a value
#   with the same quote nested in it is not matched correctly

import re
from . import regex, ranges


def index(file_string, cfscript_range=None, hidden_tags=None):
    if cfscript_range is None:
        cfscript_range = ranges.RangeWalker(file_string, 0, 'cfscript').walk()
    if hidden_tags is None:
        hidden_tags = ranges.TagText(file_string)

    functions = {}
    for name, meta in find_script_functions(file_string, cfscript_range):
        functions[name] = meta
    for name, meta in find_tag_functions(file_string, hidden_tags):
        functions[name] = meta
    return functions


def find_script_functions(file_string, cfscript_range):
    functions = []

    for m in re.finditer(regex.script_function, file_string):
        # group 5 is the func name
        if cfscript_range.is_in_range(m.start(5), ranges.NON_SCRIPT_RANGES):
            continue

        fields = [(g if g else '') for g in m.groups()]

        params_range = cfscript_range.range_at_pt(m.end())
        fields.append(split_parameters(file_string, params_range))

        attributes = ''
        func_body_range = params_range.parent.next_child_range(
            params_range.end, ['curly_brackets', 'semicolon']
        )
        if func_body_range:
            attributes = file_string[params_range.end : func_body_range.start]
            fields.append(attributes)
        else:
            fields.append('')

        functions.append(parse_script_function(regex.ScriptFunction._make(fields)))
    return functions


def split_parameters(file_string, params_range):
    # the source text of each parameter, split at the commas of the
    # parameter list; a comment between parameters is left out, so that its
    # words are not read as a type, a name or attributes
    parameters = []
    parameter = ''
    r_start = params_range.start + 1
    for child_range in params_range.children:
        if child_range.name == 'comma':
            parameters.append(parameter + file_string[r_start : child_range.start])
            parameter = ''
            r_start = child_range.end
        elif child_range.name in ['line_comment', 'multiline_comment']:
            parameter += file_string[r_start : child_range.start] + ' '
            r_start = child_range.end
    parameters.append(parameter + file_string[r_start : params_range.end - 1])
    return parameters


def parse_script_function(script_function):
    def parse_storage_slot(slot):
        if slot.lower() in ['public', 'private', 'remote', 'package']:
            return 'access'
        elif slot.lower() in ['static', 'final', 'abstract']:
            return 'modifier'

    function = {}

    # modifiers can come before and after the return type, in any order
    modifiers = script_function.modifiers_before + script_function.modifiers_after
    for slot in modifiers.split():
        key = parse_storage_slot(slot)
        function[key] = slot
    if 'access' not in function:
        function['access'] = 'public'

    function['returntype'] = (
        script_function.returntype if len(script_function.returntype) else None
    )

    docblock = parse_docblock(script_function.docblock)
    function['parameters'] = parse_script_function_parameters(
        script_function.parameters, docblock
    )

    param_names = [param['name'].lower() for param in function['parameters']]
    for key in docblock:
        if key in param_names:
            continue

        for d in docblock[key]:
            if key == 'param' and split_param_tag(d)[0] in param_names:
                continue
            full_key = (
                d.key.lower() + '.' + d.subkey.lower()
                if len(d.subkey) > 0
                else d.key.lower()
            )
            function[full_key] = d.value.strip()

    function.update(parse_attributes(script_function.attributes))

    return (script_function.name, function)


def parse_script_function_parameters(parameters, docblock):
    params = []
    for s in parameters:
        # a destructuring pattern, `{a, b: {c}} = {}`, is one parameter named
        # by its source text, so it is swapped out for a placeholder name
        pattern = None
        pattern_span = find_parameter_pattern(s)
        if pattern_span:
            pattern = s[pattern_span[0] : pattern_span[1]]
            s = s[: pattern_span[0]] + '__pattern__' + s[pattern_span[1] :]

        m = regex.script_parameter.search(s)
        if m is None:
            continue
        script_parameter = regex.ScriptParameter._make(m.groups())

        # a struct, array or parenthesized default ends at its own closing
        # bracket, not at the first one nested in it
        if script_parameter.default and script_parameter.default[0] in BRACKET_RANGES:
            default_end = find_bracket_end(s, m.start('default'))
            script_parameter = script_parameter._replace(
                default=s[m.start('default') : default_end], attributes=s[default_end:]
            )
        parameter = {}
        parameter['required'] = True if script_parameter.required else False
        parameter['type'] = script_parameter.type
        parameter['default'] = (
            script_parameter.default.strip() if script_parameter.default else None
        )

        for d in parameter_docblock(docblock, script_parameter.name):
            key = d.subkey.lower() if len(d.subkey) else 'hint'
            # a bare `@name` tag gives the parameter no hint
            if key == 'hint' and not d.value.strip():
                continue
            parameter[key] = d.value.strip()

        parameter.update(parse_attributes(script_parameter.attributes))

        parameter['name'] = script_parameter.name
        if pattern:
            parameter['name'] = re.sub(r'\s+', ' ', pattern)
            parameter['destructuring'] = True
        if script_parameter.rest:
            parameter['rest'] = True
        params.append(parameter)
    return params


def parameter_docblock(docblock, name):
    # the docblock tags of a parameter: `@name text`, `@name.key text`, and
    # `@param name text`
    tags = list(docblock.get(name.lower(), []))
    for d in docblock.get('param', []):
        param_name, text = split_param_tag(d)
        if param_name == name.lower():
            tags.append(d._replace(value=text))
    return tags


def split_param_tag(docblock_tag):
    # the lower case name of the parameter a `@param name text` tag is
    # for, and its text
    words = docblock_tag.value.split(None, 1)
    if len(words) == 0:
        return '', ''
    return words[0].lower(), words[1] if len(words) > 1 else ''


def find_parameter_pattern(parameter_string):
    # the span of the destructuring pattern a parameter starts with, if any
    m = regex.parameter_pattern_start.match(parameter_string)
    if m is None:
        return None
    return m.end(), find_bracket_end(parameter_string, m.end())


BRACKET_RANGES = {'{': 'curly_brackets', '[': 'square_brackets', '(': 'parentheses'}


def find_bracket_end(parameter_string, pos):
    # the end of the brackets that open at pos, or of the string if they do
    # not close; the range walker skips the strings and brackets nested in
    # them
    range_name = BRACKET_RANGES[parameter_string[pos]]
    bracket_range = ranges.RangeWalker(parameter_string, pos, range_name).walk()
    return bracket_range.end if bracket_range else len(parameter_string)


def parse_attributes(attributes_string):
    attributes = [
        regex.Attribute._make(t) for t in re.findall(regex.attribute, attributes_string)
    ]
    attr_dict = {}
    for attr in attributes:
        if len(attr.value) > 0:
            attr_dict[attr.key.lower()] = attr.value
        elif len(attr.unquoted_value) > 0:
            attr_dict[attr.key.lower()] = attr.unquoted_value
        else:
            attr_dict[attr.key.lower()] = ''
    return attr_dict


def parse_docblock(docblock_string):
    docblock = {}
    # a comment that opens with three or more stars, as a banner such as
    # /****** SUITES ******/ does, is not a docblock
    if docblock_string.startswith('*'):
        return docblock
    hint = []
    # a tag's text runs on over the lines up to the next tag, and the
    # lines before the first tag are the hint
    tags = []
    text = hint
    for docblock_line in docblock_string.split('\n'):
        m = regex.docblock.match(docblock_line)
        if m is None:
            continue
        line = regex.Docblock._make(m.groups(''))
        if len(line.key) > 0:
            text = []
            tags.append((line, text))
        if line.value.strip():
            text.append(line.value.strip())
    for line, text in tags:
        # a bare @hint is no hint, and leaves the text above the tags
        if line.key.lower() == 'hint' and len(line.subkey) == 0 and len(text) == 0:
            continue
        if line.key.lower() not in docblock:
            docblock[line.key.lower()] = []
        docblock[line.key.lower()].append(line._replace(value='\n'.join(text)))
    if len(hint) > 0 and 'hint' not in docblock:
        # a hint is text: the docs escape it and show its line breaks
        docblock['hint'] = [regex.Docblock('hint', '', '\n'.join(hint))]

    return docblock


def find_tag_functions(file_string, hidden_tags):
    functions = []
    for function_start_tag in re.finditer(regex.function_start_tag, file_string):
        if hidden_tags.contains(function_start_tag.start()):
            continue

        for function_end_tag in re.finditer(
            regex.function_end_tag, file_string[function_start_tag.start() :]
        ):
            if not hidden_tags.contains(
                function_start_tag.start() + function_end_tag.start()
            ):
                break
        else:
            continue

        function = {}
        function_start_index, function_end_index = (
            function_start_tag.start(),
            function_start_tag.start() + function_end_tag.end(),
        )
        function_string = file_string[function_start_index:function_end_index]
        function_tag_string = function_start_tag.group(1)

        function.update(parse_attributes(function_tag_string))

        if 'name' not in function:
            print(
                'CFML: could not find function name while indexing...\n'
                + function_string
            )
            continue

        if 'access' not in function:
            function['access'] = 'public'

        if 'returntype' not in function:
            function['returntype'] = None

        function['parameters'] = parse_tag_function_parameters(
            function_string, function_start_index, hidden_tags
        )

        function_name = function['name']
        del function['name']

        functions.append((function_name, function))

    return functions


def parse_tag_function_parameters(function_string, function_start_index, hidden_tags):
    parameters = []
    for m in re.finditer(regex.argument_tag, function_string):
        if hidden_tags.contains(function_start_index + m.start()):
            continue

        parameter_string = m.group(1)
        parameter = {}
        parameter.update(parse_attributes(parameter_string))

        if 'name' not in parameter:
            print('CFML: could not find parameter name while indexing...\n' + m.group())
            continue

        if 'required' in parameter and parameter['required'].lower() in ['true', 'yes']:
            parameter['required'] = True
        else:
            parameter['required'] = False

        if 'type' not in parameter:
            parameter['type'] = None

        if 'default' in parameter:
            if parameter['default'].startswith('#') and parameter['default'].endswith(
                '#'
            ):
                parameter['default'] = parameter['default'][1:-1]
        else:
            parameter['default'] = None

        parameters.append(parameter)

    return parameters
