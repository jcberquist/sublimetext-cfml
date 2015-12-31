# This module, via load_directory(), takes in a directory path and recursively
# browses it and its subfolders looking for ".cfc" files, and
# then uses the functionfinder module to load the functions from those files. It assumes
# that all such files in the directory are model (e.g. component) files, and does not
# check that the files actually define components. It returns a dict of bean names mapped to
# a named tuple containing function metadata and completions. The bean names are determined
# by the get_bean_names() function, or by an alternative function passed in to load_directory()

# The returned dict structure looks like this:
# {
#   "beanname": Bean(file_path, metadata, completions),
#   ...
# }

import os
from .functionfinder import find_functions
from collections import namedtuple
Bean = namedtuple('Bean', 'file_path functions completions')

def get_bean_names(root_path, file_path):
	bean_path, file_ext = os.path.splitext(file_path)
	bean_path = bean_path.replace("\\","/").replace(root_path.replace("\\","/"),'').split('/')
	bean_name = bean_path.pop().lower()
	bean_folder = bean_path.pop().lower().capitalize() if len(bean_path) > 0 else ""
	return [bean_name, bean_name + (bean_folder if len(bean_folder) == 0 or bean_folder[-1] != "s" else bean_folder[:-1])]

def load_directory(root_path, bean_names_func=get_bean_names):
	beans = {}
	file_count = 0
	for path, directories, filenames in os.walk(root_path):
		for filename in filenames:
			bean_name, file_ext = os.path.splitext(filename)
			if file_ext == ".cfc":
				file_count += 1
				full_file_path = path.replace("\\","/") + "/" + filename
				bean_names = bean_names_func(root_path, full_file_path)
				beans.update(load_file(full_file_path, bean_names))
	return (beans, file_count)

def load_file(file_path, bean_names):
	try:
		with open(file_path, 'r') as f:
			file_string = f.read()
	except:
		print("CFML: unable to read file: " + file_path)
		return {}
	functions = find_functions(file_string)
	beans = {bean_name.lower(): Bean(file_path, make_metadata(bean_name, functions), make_completions(bean_name, functions)) for bean_name in bean_names}
	return beans

def make_completions(bean_name, functions):
	return [make_completion(bean_name, function_name, function_params) for function_name, function_params in functions]

def make_metadata(bean_name, functions):
	return {function_name.lower(): (function_name, function_params)  for function_name, function_params in functions}

def make_completion(bean_name, function_name, function_params):
	key_string = function_name + "()"
	if function_params["returntype"]:
		key_string += ":" + function_params["returntype"]
	return (key_string + "\t(" + bean_name + ")", function_name + "(" + make_arguments_string(function_params["arguments"]) + ")")

def make_arguments_string(arguments):
	index = 1
	delim = ""
	arguments_string = ""
	for argument_name, argument_params in arguments:
		if argument_params["required"] or index == 1:
			arguments_string += delim + "${" + str(index) + ":" + make_argument_string(argument_name, argument_params) + "}"
			index += 1
		else:
			arguments_string += "${" + str(index) + ":, ${" + str(index + 1) +":" + make_argument_string(argument_name, argument_params) + "}}"
			index += 2
		delim = ', '
	return arguments_string

def make_argument_string(argument_name, argument_params):
	argument_string = "required " if argument_params["required"] else ""
	if argument_params["type"]:
		argument_string += argument_params["type"] + " "
	argument_string += argument_name
	if argument_params["default"]:
		argument_string += "=" + argument_params["default"]
	return argument_string
