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
#         "default": "defaultvalue" or None
#       },
#       ...
#     ]
#   },
#   ...
# }

# Known Limitations:
# - similarly tag function attributes are matched on opening and closing quotes and if quotes
#   are nested they will not be matched correctly

import re
from . import regex, ranges


def index(file_string, cfscript_range=None):
    if cfscript_range is None:
        cfscript_range = ranges.RangeWalker(file_string, 0, 'cfscript').walk()

    functions = {}
    for name, meta in find_script_functions(file_string, cfscript_range):
        functions[name] = meta
    for name, meta in find_tag_functions(file_string, cfscript_range):
        functions[name] = meta
    return functions


def find_script_functions(file_string, cfscript_range):
    functions = []

    for m in re.finditer(regex.script_function, file_string):
        # group 5 is the func name
        if cfscript_range.is_in_range(m.start(5), ranges.NON_SCRIPT_RANGES):
            continue

        l = [(g if g else '') for g in m.groups()]

        params_range = cfscript_range.range_at_pt(m.end())
        parameters = []
        r_start = params_range.start + 1
        for child_range in params_range.children:
            if child_range.name == 'comma':
                parameters.append(file_string[r_start:child_range.start])
                r_start = child_range.end
        parameters.append(file_string[r_start:params_range.end - 1])
        l.append(parameters)

        attributes = ''
        func_body_range = params_range.parent.next_child_range(params_range.end, ['curly_brackets', 'semicolon'])
        if func_body_range:
            attributes = file_string[params_range.end:func_body_range.start]
            l.append(attributes)
        else:
            l.append('')

        functions.append(parse_script_function(regex.ScriptFunction._make(l)))
    return functions


def parse_script_function(script_function):
    def parse_storage_slot(slot):
        if slot.lower() in ["public", "private", "remote", "package"]:
            return "access"
        elif slot.lower() in ["static", "final", "abstract"]:
            return "modifier"

    function = {}

    if len(script_function.storage_slot_1) > 0:
        key = parse_storage_slot(script_function.storage_slot_1)
        function[key] = script_function.storage_slot_1
    if len(script_function.storage_slot_2) > 0:
        key = parse_storage_slot(script_function.storage_slot_2)
        function[key] = script_function.storage_slot_2
    if "access" not in function:
        function["access"] = "public"

    function["returntype"] = script_function.returntype if len(script_function.returntype) else None

    docblock = parse_docblock(script_function.docblock)
    function["parameters"] = parse_script_function_parameters(script_function.parameters, docblock)

    param_names = [param["name"].lower() for param in function["parameters"]]
    for key in docblock:
        if key in param_names:
            continue

        for d in docblock[key]:
            full_key = d.key.lower() + '.' + d.subkey.lower() if len(d.subkey) > 0 else d.key.lower()
            function[full_key] = d.value.strip()

    function.update(parse_attributes(script_function.attributes))

    return (script_function.name, function)


def parse_script_function_parameters(parameters, docblock):
    params = []
    for s in parameters:
        m = regex.script_parameter.search(s)
        if m is None:
            continue
        script_parameter = regex.ScriptParameter._make(m.groups())
        parameter = {}
        parameter["required"] = True if script_parameter.required else False
        parameter["type"] = script_parameter.type
        parameter["default"] = script_parameter.default.strip() if script_parameter.default else None

        for d in docblock.get(script_parameter.name.lower(), []):
            key = d.subkey.lower() if len(d.subkey) else "hint"
            parameter[key] = d.value.strip()

        parameter.update(parse_attributes(script_parameter.attributes))

        parameter["name"] = script_parameter.name
        params.append(parameter)
    return params


def parse_function_attributes(attributes_string):
    # remove strings
    strings = {}
    for i, s in enumerate(re.findall(regex.strings, attributes_string)):
        key = r"__string_" + str(i) + "__"
        strings[key] = s
        attributes_string = attributes_string.replace(s, key)

    # perform search
    try:
        attributes_string = re.search(regex.function_attributes, attributes_string).group(1)
    except:
        print(attributes_string)

    # add strings back
    for key in strings:
        attributes_string = attributes_string.replace(key, strings[key])
    return parse_attributes(attributes_string)


def parse_attributes(attributes_string):
    attributes = [regex.Attribute._make(t) for t in re.findall(regex.attribute, attributes_string)]
    attr_dict = {}
    for attr in attributes:
        if len(attr.value) > 0:
            attr_dict[attr.key.lower()] = attr.value
        elif len(attr.unquoted_value) > 0:
            attr_dict[attr.key.lower()] = attr.unquoted_value
        else:
            attr_dict[attr.key.lower()] = ""
    return attr_dict


def parse_docblock(docblock_string):
    docblock = {}
    hint = []
    for t in re.findall(regex.docblock, docblock_string):
        line = regex.Docblock._make(t)
        if len(line.key) == 0:
            hint.append(line.value.strip())
        else:
            if line.key.lower() not in docblock:
                docblock[line.key.lower()] = []
            docblock[line.key.lower()].append(line)
    if len(hint) > 0 and "hint" not in docblock:
        docblock["hint"] = [regex.Docblock("hint", "", "<br>".join(hint))]

    return docblock


def find_tag_functions(file_string, cfscript_range):
    functions = []
    for function_start_tag in re.finditer(regex.function_start_tag, file_string):
        if cfscript_range.is_in_range(function_start_tag.start(), ranges.NON_SCRIPT_RANGES):
            continue

        for function_end_tag in re.finditer(regex.function_end_tag, file_string[function_start_tag.start():]):
            if not cfscript_range.is_in_range(function_start_tag.start() + function_end_tag.start(), ranges.NON_SCRIPT_RANGES):
                break
        else:
            continue

        function = {}
        function_start_index, function_end_index = function_start_tag.start(), function_start_tag.start() + function_end_tag.end()
        function_string = file_string[function_start_index:function_end_index]
        function_tag_string = function_start_tag.group(1)

        function.update(parse_attributes(function_tag_string))

        if "name" not in function:
            print("CFML: could not find function name while indexing...\n" + function_string)
            continue

        if "access" not in function:
            function["access"] = "public"

        if "returntype" not in function:
            function["returntype"] = None

        function["parameters"] = parse_tag_function_parameters(function_string, function_start_index, cfscript_range)

        function_name = function["name"]
        del function["name"]

        functions.append((function_name, function))

    return functions


def parse_tag_function_parameters(function_string, function_start_index, cfscript_range):
    parameters = []
    for m in re.finditer(regex.argument_tag, function_string):
        if cfscript_range.is_in_range(function_start_index + m.start(), ranges.NON_SCRIPT_RANGES):
            continue

        parameter_string = m.group()
        parameter = {}
        parameter.update(parse_attributes(parameter_string))

        if "name" not in parameter:
            print("CFML: could not find parameter name while indexing...\n" + parameter_string)
            continue

        if "required" in parameter and parameter["required"].lower() in ["true", "yes"]:
            parameter["required"] = True
        else:
            parameter["required"] = False

        if "type" not in parameter:
            parameter["type"] = None

        if "default" in parameter:
            if (
                parameter["default"].startswith("#")
                and parameter["default"].endswith("#")
            ):
                parameter["default"] = parameter["default"][1:-1]
        else:
            parameter["default"] = None

        parameters.append(parameter)

    return parameters
