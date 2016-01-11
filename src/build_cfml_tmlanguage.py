import sublime, sublime_plugin
import os, plistlib, shutil
from . import utils

CFOUTPUT_INJECTION = {
	"patterns": [
	  {
	  	"match": "##", "name": "constant.character.escape.hash.cfml"
		},
	  {
	  	"begin": "#", "beginCaptures": {"0":{"name": "constant.character.hash.cfml.start"}},
	  	"end": "#", "endCaptures": {"0":{"name": "constant.character.hash.cfml.end"}},
	  	"contentName": "source.cfml.script", "patterns": [{"include": "#source-cfml-script"}]
		},
		{
			"include": "#cfml-tags"
		}
	]
}

############################################

def get_setting(key):
	package_settings = sublime.load_settings("cfml_package.sublime-settings")
	return package_settings.get(key)

def create_directory_if_not_exists(directory_path):
	if os.path.exists(directory_path):
		return True

	try:
		os.makedirs(directory_path)
		print("CFML: created directory - " + directory_path)
		return True
	except:
		print("CFML: unable to create directory - " + directory_path)
		return False

def prefix_includes(pattern, prefix):
	new_pattern = dict(pattern)
	if "include" in new_pattern and new_pattern["include"].startswith("#"):
		new_pattern["include"] = "#" + prefix + "-" + new_pattern["include"][1:]
	if "patterns" in new_pattern:
		new_pattern["patterns"] = [prefix_includes(pattern, prefix) for pattern in new_pattern["patterns"]]
	if "repository" in new_pattern:
		new_pattern["repository"] = {prefix + "-" + k: prefix_includes(v, prefix) for k, v in new_pattern["repository"].items()}
	return new_pattern

def rename_include(pattern, source_include, target_include):
	new_pattern = dict(pattern)
	if "include" in new_pattern and new_pattern["include"] == source_include:
		new_pattern["include"] = target_include
	if "patterns" in new_pattern:
		new_pattern["patterns"] = [rename_include(pattern, source_include, target_include) for pattern in new_pattern["patterns"]]
	if "repository" in new_pattern:
		new_pattern["repository"] = {k: rename_include(v, source_include, target_include) for k, v in new_pattern["repository"].items()}
	return new_pattern

def merge_into_syntax(syntax_to_merge, target_syntax):
	syntax_key = syntax_to_merge["scopeName"].replace(".","-")
	target_syntax = rename_include(target_syntax, syntax_to_merge["scopeName"], "#" + syntax_key)
	syntax_to_merge = prefix_includes(syntax_to_merge, syntax_key)
	syntax_to_merge = rename_include(syntax_to_merge, "$self", "#" + syntax_key)

	if "repository" in syntax_to_merge:
		target_syntax["repository"].update(syntax_to_merge["repository"])

	target_syntax["repository"][syntax_key] = {"patterns": syntax_to_merge["patterns"]}
	return target_syntax

def filter_pattern(pattern, scopes_to_remove):
	def is_valid(p):
		return "include" not in p or p["include"] not in scopes_to_remove

	result = dict(pattern)
	if "patterns" in result:
		result["patterns"] = [filter_pattern(pattern, scopes_to_remove) for pattern in result["patterns"] if is_valid(pattern)]
	return result

def filter_syntax(syntax, scope_key):
	scopes_to_remove = [scope_key] + [item["include"] for item in syntax["repository"][scope_key[1:]]["patterns"]]
	for s in scopes_to_remove:
		del syntax["repository"][s[1:]]
	syntax = filter_pattern(syntax, scopes_to_remove)
	syntax["repository"] = {k: filter_pattern(v, scopes_to_remove) for k, v in syntax["repository"].items()}
	return syntax

def inject_include_into_pattern(pattern, scope_key):
	new_pattern = dict(pattern)
	if "patterns" in new_pattern:
		new_pattern["patterns"] = [{"include": scope_key}] + [inject_include_into_pattern(pattern, scope_key) for pattern in new_pattern["patterns"]]
	return new_pattern

def inject_include_into_syntax(syntax, scope_key):
	syntax["patterns"] = [inject_include_into_pattern(pattern, scope_key) for pattern in syntax["patterns"]]
	if "repository" in syntax:
		syntax["repository"] = {k: inject_include_into_pattern(v, scope_key) for k, v in syntax["repository"].items()}
	return syntax

def load_plist(relative_path):
	try:
		plist_data = plistlib.readPlistFromBytes(sublime.load_binary_resource(relative_path))
		print("CFML: loaded plist file - " + relative_path)
		return plist_data
	except:
		print("CFML: unable to load plist file - " + relative_path)
		return None

class CfmlBuildTmlanguageCommand(sublime_plugin.ApplicationCommand):

	def run(self):
		print("CFML: building cfml.tmLanguage")

		# cfml
		cfml = load_plist("Packages/" + utils.get_plugin_name() + "/syntaxes/cfml.plist")
		cfscript = load_plist("Packages/" + utils.get_plugin_name() + "/syntaxes/cfscript.plist")

		# html
		html = load_plist(get_setting("tmlanguage_html"))
		if not html:
			sublime.message_dialog("CFML: unable to build cfml.tmLanguage - see console for details")
			return
		print("CFML: building text.html.cfml")
		html = filter_syntax(html, "#embedded-code")

		text_html_cfml = dict(html)
		text_html_cfml["scopeName"] = "text.html.cfml"
		text_html_cfml = inject_include_into_syntax(text_html_cfml, "#cfml")

		text_html_cfml_output = dict(html)
		text_html_cfml_output["scopeName"] = "text.html.cfml.cfoutput"
		text_html_cfml_output = rename_include(text_html_cfml_output, "source.js", "source.js.cfoutput")
		text_html_cfml_output = rename_include(text_html_cfml_output, "source.css", "source.css.cfoutput")
		text_html_cfml_output = inject_include_into_syntax(text_html_cfml_output, "#cfml")

		# javascript
		javascript = load_plist(get_setting("tmlanguage_javascript"))
		if not javascript:
			sublime.message_dialog("CFML: unable to build cfml.tmLanguage - see console for details")
			return
		print("CFML: building source.js")

		javascript_cfml = dict(javascript)
		javascript_cfml = inject_include_into_syntax(javascript_cfml, "#cfml")

		javascript_cfml_output = dict(javascript)
		javascript_cfml_output["scopeName"] = "source.js.cfoutput"
		javascript_cfml_output = inject_include_into_syntax(javascript_cfml_output, "#cfml")

		# css
		css = load_plist(get_setting("tmlanguage_css"))
		if not css:
			sublime.message_dialog("CFML: unable to build cfml.tmLanguage - see console for details")
			return
		print("CFML: building source.css")

		css_cfml = dict(css)
		css_cfml = inject_include_into_syntax(css_cfml, "#cfml")

		css_cfml_output = dict(css)
		css_cfml_output["scopeName"] = "source.css.cfoutput"
		css_cfml_output = inject_include_into_syntax(css_cfml_output, "#cfml")

		# sql
		sql = load_plist(get_setting("tmlanguage_sql"))
		if not sql:
			sublime.message_dialog("CFML: unable to build cfml.tmLanguage - see console for details")
			return
		print("CFML: building source.sql")
		# remove single line string matches as they do not allow pattern injection
		sql["repository"]["strings"]["patterns"] = [pattern for pattern in sql["repository"]["strings"]["patterns"] if "patterns" in pattern]
		sql_cfml = inject_include_into_syntax(sql, "#cfml")


		# merge syntaxes
		print("CFML: merging syntaxes...")
		cfml_tmlanguage = merge_into_syntax(cfscript, cfml)
		cfml_tmlanguage = merge_into_syntax(text_html_cfml, cfml_tmlanguage)
		cfml_tmlanguage = merge_into_syntax(text_html_cfml_output, cfml_tmlanguage)
		cfml_tmlanguage = merge_into_syntax(javascript_cfml, cfml_tmlanguage)
		cfml_tmlanguage = merge_into_syntax(javascript_cfml_output, cfml_tmlanguage)
		cfml_tmlanguage = merge_into_syntax(css_cfml, cfml_tmlanguage)
		cfml_tmlanguage = merge_into_syntax(css_cfml_output, cfml_tmlanguage)
		cfml_tmlanguage = merge_into_syntax(sql_cfml, cfml_tmlanguage)

		# need to match tag comment syntax in script as script could be inline with <cfscript>
		cfml_tmlanguage["repository"]["source-cfml-script-comments"]["patterns"].append({"include": "#comments"})

		cfml_tmlanguage = rename_include(cfml_tmlanguage, "#text-html-cfml-cfml", "#cfml-tags")
		cfml_tmlanguage = rename_include(cfml_tmlanguage, "#source-js-cfml", "#cfml-tags")
		cfml_tmlanguage = rename_include(cfml_tmlanguage, "#source-css-cfml", "#cfml-tags")
		cfml_tmlanguage = rename_include(cfml_tmlanguage, "#source-sql-cfml", "#cfoutput-injection")

		cfml_tmlanguage = rename_include(cfml_tmlanguage, "#text-html-cfml-cfoutput-cfml", "#cfoutput-injection")
		cfml_tmlanguage = rename_include(cfml_tmlanguage, "#source-js-cfoutput-cfml", "#cfoutput-injection")
		cfml_tmlanguage = rename_include(cfml_tmlanguage, "#source-css-cfoutput-cfml", "#cfoutput-injection")

		cfml_tmlanguage["repository"]["cfoutput-injection"] = CFOUTPUT_INJECTION

		syntax_path = sublime.packages_path().replace("\\","/") + "/" + utils.get_plugin_name() + "/syntaxes"
		directory_exists = create_directory_if_not_exists(syntax_path)

		if not directory_exists:
			print("CFML: unable to write cfml.tmLanguage")
			sublime.message_dialog("CFML: unable to build cfml.tmLanguage - see console for details")
			return

		syntax_path += "/cfml.tmLanguage"
		print("CFML: writing plist file - " + syntax_path)
		plistlib.writePlist(cfml_tmlanguage, syntax_path)
		print("CFML: cfml.tmLanguage build complete")
		sublime.message_dialog("CFML: cfml.tmLanguage build complete")
