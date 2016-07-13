# This module, via index(), takes in a cfml source file string and
# returns a python dict of the function names mapped to a dict
# containing data about the function.

# The structure looks like this:
# {
#   "function_name": {
#     "access": "public/private/etc",
#     "returntype": "any/string/numeric/etc",
#     "arguments": [
#       { "name", "argument_name"
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
# - script function parameters are matched via opening and closing ( ), so if any parameter
#   has a default value that includes parentheses the function will not be matched correctly
# - similarly tag function attributes are matched on opening and closing quotes and if quotes
#   are nested they will not be matched correctly

import re
from . import regex


def index(file_string):
    functions = {}
    for name, meta in find_script_functions(file_string):
        functions[name] = meta
    for name, meta in find_tag_functions(file_string):
        functions[name] = meta
    return functions


def find_script_functions(file_string):
    functions = []
    for t in re.findall(regex.script_function, file_string):
        functions.append(parse_script_function(regex.ScriptFunction._make(t)))
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
    function["arguments"] = parse_script_function_arguments(script_function.arguments, docblock)

    arg_names = [arg["name"].lower() for arg in function["arguments"]]
    for key in docblock:
        if key in arg_names:
            continue
        d = docblock[key]
        full_key = d.key.lower() + '.' + d.subkey.lower() if len(d.subkey) > 0 else d.key.lower()
        function[full_key] = d.value

    function.update(parse_function_attributes(script_function.arguments))

    return (script_function.name, function)


def parse_script_function_arguments(arguments_string, docblock):
    args = []
    for t in re.findall(regex.script_argument, arguments_string):
        script_argument = regex.ScriptArgument._make(t)
        argument = {}
        argument["required"] = True if len(script_argument.required) > 0 else False
        argument["type"] = script_argument.type if len(script_argument.type) > 0 else None
        argument["default"] = script_argument.default.strip() if len(script_argument.default) else None

        for d in docblock.get(script_argument.name.lower(), []):
            key = d.subkey.lower() if len(d.subkey) else "hint"
            argument[key] = d.value.strip()

        argument.update(parse_attributes(script_argument.attributes))

        argument["name"] = script_argument.name
        args.append(argument)
    return args


def parse_function_attributes(attributes_string):
    # remove strings
    strings = {}
    for i, s in enumerate(re.findall(regex.strings, attributes_string)):
        key = r"__string_" + str(i) + "__"
        strings[key] = s
        attributes_string = attributes_string.replace(s, key)

    # perform search
    attributes_string = re.search(regex.function_attributes, attributes_string).group(1)

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
        docblock["hint"] = regex.Docblock("hint", "", "<br>".join(hint))
    return docblock


def find_tag_functions(file_string):
    functions = []
    for function_string in re.findall(regex.function_block, file_string):
        function = {}
        function_tag_string = re.search(regex.function_start_tag, function_string).group(1)
        function.update(parse_attributes(function_tag_string))

        if "name" not in function:
            print("CFML: could not find function name while indexing...\n" + function_string)
            continue

        if "access" not in function:
            function["access"] = "public"

        if "returntype" not in function:
            function["returntype"] = None

        function["arguments"] = parse_tag_function_arguments(function_string)

        function_name = function["name"]
        del function["name"]

        functions.append((function_name, function))

    return functions


def parse_tag_function_arguments(function_string):
    arguments = []
    for argument_string in re.findall(regex.argument_tag, function_string):
        argument = {}
        argument.update(parse_attributes(argument_string))

        if "name" not in argument:
            print("CFML: could not find argument name while indexing...\n" + argument_string)
            continue

        if "required" in argument and argument["required"].lower() in ["true", "yes"]:
            argument["required"] = True
        else:
            argument["required"] = False

        if "type" not in argument:
            argument["type"] = None

        if "default" in argument:
            if (
                argument["default"].startswith("#")
                and argument["default"].endswith("#")
            ):
                argument["default"] = argument["default"][1:-1]
        else:
            argument["default"] = None

        arguments.append(argument)

    return arguments
