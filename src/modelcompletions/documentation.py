STYLES = {
	"side_color": "#4C9BB0",
	"header_color": "#306B7B",
	"header_bg_color": "#E4EEF1",
	"text_color": "#272B33"
}

def get_documentation(bean_name, file_path, function_name, function_metadata):
	model_doc = dict(STYLES)
	model_doc["links"] = [{"href": "go_to_definition", "text": "Go to Definition"}]

	model_doc["header"] = bean_name + "." + function_name + "()"
	if len(function_metadata["access"]) > 0:
		model_doc["header"] = "<em>" + function_metadata["access"] + "</em> " + model_doc["header"]
	if len(function_metadata["returntype"]) > 0:
		model_doc["header"] += ":" + function_metadata["returntype"]

	model_doc["description"] = "<small>" + file_path + "</small>"

	model_doc["body"] = ""
	if len(function_metadata["arguments"]) > 0:
		model_doc["body"] += "<ul>"
		for arg_name, arg_params in function_metadata["arguments"]:
			model_doc["body"] += "<li>"
			if arg_params["required"]:
				model_doc["body"] += "required "
			if arg_params["type"]:
				model_doc["body"] += "<em>" + arg_params["type"] + "</em> "
			model_doc["body"] += "<strong>" + arg_name + "</strong>"
			if arg_params["default"]:
				model_doc["body"] += " = " + arg_params["default"]
			model_doc["body"] += "</li>"
		model_doc["body"] += "</ul>"

	return model_doc
