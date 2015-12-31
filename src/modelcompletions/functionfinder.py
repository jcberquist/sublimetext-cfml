# This module, via find_functions(), takes in a cfml source file string and
# returns a python list containing tuples of the function name and a map of data
# about the function.

# The structure looks like this:
# [
#   ("function_name", {
#     "access": "public/private/etc",
#     "returntype": "any/string/numeric/etc",
#     "arguments": [
#       ("argument_name", {
#         "required": True/False,
#         "type": "any/string/numeric/etc" or None,
#         "default": "defaultvalue" or None
#       }),
#       ...
#     ]
#   }),
#   ...
# ]

# Known Limitations:
# - script function parameters are matched via opening and closing ( ), so if any parameter
#   has a default value that includes parentheses the function will not be matched correctly
# - similarly tag function attributes are matched on opening and closing quotes and if quotes
#   are nested they will not be matched correctly

import re

script_function_regex = re.compile('(?:(private|package|public|remote)\s+)?([A-Za-z0-9_\.$]+)?\s*function\s+([_$a-zA-Z][$\w]*)\s*(?:\(\s*([^)]*)\))', re.I)
script_arguments_regex = re.compile(r'(?:^|,)\s*(required)?\s*(\b\w+\b)?\s*(\b\w+\b)(?:\s*=\s*(\{[^\}]*\}|\[[^\]]*\]|[^,\)]+))?', re.I)

function_block_regex = re.compile('<cffunction.*?</cffunction>', re.I | re.DOTALL)
function_regex = {}
function_regex["name"] = re.compile(r'<cffunction.*?name\s*=\s*(\'|")([_$a-zA-Z][$\w]*)(\1).*?>', re.I | re.DOTALL)
function_regex["access"] = re.compile(r'<cffunction.*?access\s*=\s*(\'|")([_$a-zA-Z][$\w]*)(\1).*?>', re.I | re.DOTALL)
function_regex["returntype"] = re.compile(r'<cffunction.*?returntype\s*=\s*(\'|")([_$a-zA-Z][$\w]*)(\1).*?>', re.I | re.DOTALL)

argument_block_regex = re.compile('<cfargument[^>]*>', re.I)
argument_regex = {}
argument_regex["name"] = re.compile(r'name\s*=\s*(\'|")(\w*)(\1)', re.I)
argument_regex["required"] = re.compile(r'required\s*=\s*(\'|")(\w*)(\1)', re.I)
argument_regex["default"] = re.compile(r'default\s*(=\s*(\'|")#?([^\2]*?)#?(\2))', re.I)
argument_regex["type"] = re.compile(r'type\s*=\s*(\'|")([^\1]*?)(\1)', re.I)

def find_functions(file_string):
	functions = [function_tuple for function_tuple in find_script_functions(file_string) if function_tuple[0] != "init"]
	functions.extend([function_tuple for function_tuple in find_tag_functions(file_string) if function_tuple[0] != "init"])
	return functions

def find_script_functions(file_string):
	return [find_script_function(access, returntype, function_name, arguments) for access, returntype, function_name, arguments in re.findall(script_function_regex, file_string)]

def find_script_function(access, returntype, function_name, arguments):
	function = {}
	function["access"] = access if len(access) else "public"
	function["returntype"] = returntype if len(returntype) else None
	function["arguments"] = find_script_function_arguments(arguments)
	return (function_name, function)

def find_script_function_arguments(arguments_string):
	return [find_script_function_argument(arg_required, arg_type, arg_name, arg_default) for arg_required, arg_type, arg_name, arg_default in re.findall(script_arguments_regex, arguments_string)]

def find_script_function_argument(arg_required, arg_type, arg_name, arg_default):
	argument = {}
	argument["required"] = True if len(arg_required) else False
	argument["type"] = arg_type if len(arg_type) else None
	argument["default"] = arg_default.strip() if len(arg_default) else None
	return (arg_name, argument)

def find_tag_functions(file_string):
	return [find_tag_function(function_string) for function_string in re.findall(function_block_regex,file_string)]

def find_tag_function(function_string):
	function_matches = {}
	for key in function_regex:
		function_matches[key] = re.search(function_regex[key], function_string)
	if not function_matches["name"]:
		return None
	function = {}
	function["access"] = function_matches["access"].group(2) if function_matches["access"] else "public"
	function["returntype"] = function_matches["returntype"].group(2) if function_matches["returntype"] else None
	function["arguments"] = find_tag_function_arguments(function_string)
	return (function_matches["name"].group(2), function)

def find_tag_function_arguments(function_string):
	return [find_tag_argument(argument_string) for argument_string in re.findall(argument_block_regex, function_string)]

def find_tag_argument(argument_string):
	argument_matches = {}
	for key in argument_regex:
		argument_matches[key] = re.search(argument_regex[key], argument_string)
	if not argument_matches["name"]:
		return None
	argument = {}
	argument["required"] = True if argument_matches["required"] else False
	argument["type"] = argument_matches["type"].group(2) if argument_matches["type"] else None
	argument["default"] = argument_matches["default"].group(2) if argument_matches["default"] else None
	return (argument_matches["name"].group(2), argument)
