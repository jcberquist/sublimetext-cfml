import sublime
from functools import partial
from .component_project_index import get_extended_metadata_by_file_path

STYLES = {
	"side_color": "#4C9BB0",
	"header_color": "#306B7B",
	"header_bg_color": "#E4EEF1",
	"text_color": "#272B33"
}

def open_file_at_symbol(view, file_path, symbol):
	index_locations = view.window().lookup_symbol_in_index(symbol)

	for full_path, project_path, rowcol in index_locations:
		if full_path == file_path:
			row, col = rowcol
			view.window().open_file(full_path + ":" + str(row) + ":" + str(col), sublime.ENCODED_POSITION | sublime.FORCE_GROUP)
			break
	else:
		# might be a setter, so for now just open the file
		view.window().open_file(file_path)

def on_navigate(view, file_path, function_file_map, href):
	if href == "__go_to_component":
		if file_path[1] == ":":
			file_path = "/" + file_path[0] + file_path[2:]
		view.window().open_file(file_path)
	else:
		file_path = function_file_map[href.lower()]
		if file_path[1] == ":":
			file_path = "/" + file_path[0] + file_path[2:]
		open_file_at_symbol(view, file_path, href)

def get_documentation(view, project_name, file_path, header):
	extended_metadata = get_extended_metadata_by_file_path(project_name, file_path)

	model_doc = dict(STYLES)
	model_doc["links"] = []

	model_doc["header"] = header
	model_doc["description"] = "<strong>path</strong>: <a class=\"alt-link\" href=\"__go_to_component\">" + file_path + "</a>"

	for key in ["entityname","extends"]:
		if extended_metadata[key]:
			model_doc["description"] += "<br><strong>" + key + "</strong>: " + extended_metadata[key]

	for key in ["accessors","persistent"]:
		if extended_metadata[key]:
			model_doc["description"] += "<br><strong>" + key + "</strong>: true"

	model_doc["body"] = ""
	if len(extended_metadata["properties"]) > 0:
		properties = parse_properties(file_path, extended_metadata)
		if len(properties) > 0:
			model_doc["body"] += "<h2>Properties</h2>"
			model_doc["body"] += "<div class=\"property-box\">"
			model_doc["body"] += "</div><div class=\"property-box\">".join(properties)
			model_doc["body"] += "</div>"

	if len(extended_metadata["functions"]) > 0:
		functions = parse_functions(file_path, extended_metadata)
		if "constructor" in functions:
			# we have a constructor
			model_doc["body"] += "<h2>Constructor</h2>"
			model_doc["body"] += "<div class=\"method-box\">" + functions["constructor"] + "</div>"

		if len(functions["public"]) > 0:
			model_doc["body"] += "<h2>Public Methods</h2>"
			model_doc["body"] += "<div class=\"method-box\">"
			model_doc["body"] += "</div><div class=\"method-box\">".join(functions["public"])
			model_doc["body"] += "</div>"

		if len(functions["private"]) > 0:
			model_doc["body"] += "<h2>Private Methods</h2>"
			model_doc["body"] += "<div class=\"method-box\">"
			model_doc["body"] += "</div><div class=\"method-box\">".join(functions["private"])
			model_doc["body"] += "</div>"

	callback = partial(on_navigate, view, file_path, extended_metadata["function_file_map"])
	return model_doc, callback

def get_method_documentation(view, project_name, file_path, function_name, header):
	extended_metadata = get_extended_metadata_by_file_path(project_name, file_path)
	function_file_path = extended_metadata["function_file_map"][function_name]

	funct = extended_metadata["functions"][function_name]
	model_doc = dict(STYLES)
	model_doc["links"] = [{"href": funct.name, "text": "Go to Definition"}]

	model_doc["header"] = header
	if funct.meta["access"] and len(funct.meta["access"]) > 0:
		model_doc["header"] = "<em>" + funct.meta["access"] + "</em> " + model_doc["header"]
	if funct.meta["returntype"] and len(funct.meta["returntype"]) > 0:
		model_doc["header"] += ":" + funct.meta["returntype"]

	model_doc["description"] = "<small>" + function_file_path + "</small>"

	model_doc["body"] = ""
	if len(funct.meta["arguments"]) > 0:
		model_doc["body"] += "<ul>"
		for arg in funct.meta["arguments"]:
			model_doc["body"] += "<li>"
			if arg["required"]:
				model_doc["body"] += "required "
			if arg["type"]:
				model_doc["body"] += "<em>" + arg["type"] + "</em> "
			model_doc["body"] += "<strong>" + arg["name"] + "</strong>"
			if arg["default"]:
				model_doc["body"] += " = " + arg["default"]
			model_doc["body"] += "</li>"
		model_doc["body"] += "</ul>"

	callback = partial(on_navigate, view, file_path, extended_metadata["function_file_map"])
	return model_doc, callback

def parse_functions(file_path, metadata):
	result = {}
	constructor = metadata["initmethod"].lower() if metadata["initmethod"] else "init"
	functions = metadata["functions"]
	function_file_map = metadata["function_file_map"]
	public_functions = [(functions[key], function_file_map[key]) for key in sorted(functions) if key != constructor and is_public_function(functions[key])]
	private_functions = [(functions[key], function_file_map[key]) for key in sorted(functions) if key != constructor and not is_public_function(functions[key])]
	result["public"] = [parse_function(function, funct_file_path, file_path) for function, funct_file_path in public_functions]
	result["private"] = [parse_function(function, funct_file_path, file_path) for function, funct_file_path in private_functions]
	if constructor in functions:
		result["constructor"] = parse_function(functions[constructor], function_file_map[constructor], file_path)
	return result

def is_public_function(function):
	if function.meta["access"] and function.meta["access"] == "private":
		return False
	return True

def parse_function(function, funct_file_path, file_path):
	result = "<a class=\"alt-link\" href=\"" + function.name + "\">"
	result += function.name + "(" + ("..." if function.meta["arguments"] else "") + ")"
	if function.meta["returntype"]:
		result += ":" + function.meta["returntype"]
	result += "</a>"
	if funct_file_path != file_path:
		result += " <small><em>(from " + funct_file_path.split("/")[-1] + ")</em></small>"

	arg_strings = []
	for arg in function.meta["arguments"]:
		arg_string = ""
		if arg["required"]:
			arg_string += "required "
		if arg["type"]:
			arg_string += "<em>" + arg["type"] + "</em> "
		arg_string += "<strong>" + arg["name"] + "</strong>"
		if arg["default"]:
			arg_string += " = " + arg["default"]
		arg_strings.append(arg_string)

	if len(arg_strings) > 0:
		result += "<ul class=\"method-args\"><li>" + "</li><li>".join(arg_strings) + "</li></ul>"

	return result

def parse_properties(file_path, metadata):
	properties = metadata["properties"]
	property_file_map = metadata["property_file_map"]
	sorted_properties = [(properties[key], property_file_map[key]) for key in sorted(properties)]
	return [parse_property(prop, prop_file_path, file_path) for prop, prop_file_path in sorted_properties]


def parse_property(prop, prop_file_path, file_path):
	result = prop.name + ":<em>" + prop.meta["type"] + "</em>"
	if prop_file_path != file_path:
		result += " <small><em>(from " + prop_file_path.split("/")[-1] + ")</em></small>"
	accessors = [key for key in ["setter","getter"] if prop.meta[key]]
	if accessors:
		result += "<br><small><strong>accessors</strong>: <em>" + ", ".join(accessors) + "</em></small>"
	return result
