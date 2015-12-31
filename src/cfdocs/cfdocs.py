import sublime, json, urllib
from .. import utils
from ..inline_documentation import Documentation

CFDOCS_PARAM_TEMPLATE = '<strong>${name}</strong><p>${description}</p><p>${values}</p>'
CFDOCS_BASE_URL = "https://raw.githubusercontent.com/foundeo/cfdocs/master/data/en/"

CFDOCS_STYLES = {
	"side_color": "#18BC9C",
	"header_color": "#C7254E",
	"header_bg_color": "#F9F2F4",
	"text_color": "#272B33"
}

def get_inline_documentation(view, position):
	doc_name = None
	doc_priority = 0

	# functions
	if view.match_selector(position, "meta.support.function-call.cfml"):
		doc_name, function_name_region, function_args_region = utils.get_function_call(view, position, support_function = True)

	# tags
	elif view.match_selector(position, "meta.tag.cfml,meta.tag.script.cfml"):
		doc_name = utils.get_tag_name(view, position)
		if doc_name and doc_name[:2] != "cf":
			# tag in script
			doc_name = "cf" + doc_name

	# script component, interface, function
	elif view.match_selector(position, "meta.class.cfml"):
		doc_name = "cfcomponent"
	elif view.match_selector(position, "meta.interface.cfml"):
		doc_name = "cfinterface"
	elif view.match_selector(position, "meta.function.cfml"):
		doc_name = "cffunction"

	if doc_name:
		return get_cfdoc(doc_name, doc_priority)

	return None

def get_cfdoc(function_or_tag, doc_priority):
	data, success = fetch_cfdoc(function_or_tag)
	if success:
		return Documentation(build_cfdoc(function_or_tag, data), None, doc_priority)
	return Documentation(build_cfdoc_error(function_or_tag, data), None, doc_priority)

def fetch_cfdoc(function_or_tag):
	full_url = CFDOCS_BASE_URL + function_or_tag  + ".json"

	try:
		json_string = urllib.request.urlopen(full_url).read().decode("utf-8")
	except urllib.error.HTTPError as e:
		data = {"error_message": "Unable to fetch " + function_or_tag + ".json<br>" + str(e)}
		return data, False

	try:
		data = json.loads(json_string)
	except ValueError as e:
		data = {"error_message": "Unable to decode " + function_or_tag + ".json<br>ValueError: " + str(e)}
		return data, False

	return data, True

def build_cfdoc(function_or_tag, data):
	cfdoc = dict(CFDOCS_STYLES)
	cfdoc["links"] = [{"href": "http://cfdocs.org" + "/" + function_or_tag, "text": "cfdocs.org" + "/" + function_or_tag}]
	cfdoc["header"] = data["syntax"].replace("<","&lt;").replace(">","&gt;")
	cfdoc["description"] = data["description"].replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")

	if len(data["returns"]) > 0:
		cfdoc["header"] += ":" + data["returns"]

	cfdoc["body"] = ""
	if len(data["params"]) > 0:
		cfdoc["body"] = "<ul>"
		for param in data["params"]:
			param_variables = {"name": param["name"], "description": param["description"].replace("\n","<br>"), "values": ""}
			if len(param["values"]):
				param_variables["values"] = "<em>values:</em> " + ", ".join([str(value) for value in param["values"]])
			cfdoc["body"] += "<li>" + sublime.expand_variables(CFDOCS_PARAM_TEMPLATE, param_variables) + "</li>"
		cfdoc["body"] += "</ul>"

	return cfdoc

def build_cfdoc_error(function_or_tag, data):
	cfdoc = dict(CFDOCS_STYLES)
	cfdoc["side_color"] = "#F2777A"
	cfdoc["header_bg_color"] = "#FFFFFF"
	cfdoc["header"] = "Uh oh!"
	cfdoc["description"] = "I tried to load that doc for you but got this instead:"
	cfdoc["body"] = data["error_message"]

	return cfdoc
