from .. import utils, model_index
from ..model_index.completions import build_file_completions
from ..completions import CompletionList
from . import metadata

def get_script_completions(view, prefix, position, info):
	extended_meta = metadata.get_view_metadata(view)
	completions = build_file_completions(extended_meta)
	completions = [make_completion(completion, info["file_path"]) for completion in completions["functions"]]
	if len(completions) > 0:
		return CompletionList(completions, 2, False)
	return None

def get_dot_completions(view, prefix, position, info):
	if len(info["dot_context"]) == 0:
		return None

	for symbol in info["dot_context"]:
		if not symbol.is_function:
			if symbol.name == "this":
				extended_meta = metadata.get_view_metadata(view)
				completions = build_file_completions(extended_meta)
				completions = [make_completion(completion, info["file_path"]) for completion in completions["functions"]]
				return CompletionList(completions, 1, True)

			if len(info["dot_context"]) == 1 and symbol.name == "arguments":
				current_function_body = utils.get_current_function_body(view, position, component_method=False)
				if current_function_body:
					function = utils.get_function(view, current_function_body.begin() - 1)
					meta = metadata.get_string_metadata(view.substr(function[2]) + "{}")
					if "functions" in meta and function[0] in meta["functions"]:
						args = meta["functions"][function[0]].meta["arguments"]
						completions = [(arg["name"] + "\targuments", arg["name"]) for arg in args]
						return CompletionList(completions, 1, True)

			if symbol.name == "super" and info["project_name"]:
				extends = get_extends(view)
				if extends:
					comp = model_index.get_completions_by_dot_path(info["project_name"], extends)

					if not comp and info["file_path"]:
						extends_file_path = model_index.resolve_path(info["project_name"], info["file_path"], extends)
						comp = model_index.get_completions_by_file_path(info["project_name"], extends_file_path)

					if comp:
						completions = [(completion.key + "\t" + completion.file_path.split("/").pop(), completion.content) for completion in comp["functions"]]
						return CompletionList(completions, 1, True)

	return None

def make_completion(comp, file_path):
	hint = "this"
	if len(comp.file_path) > 0 and comp.file_path != file_path:
		hint = comp.file_path.split("/").pop()
	return (comp.key + "\t" + hint, comp.content)

def get_extends(view):
	extends_regions = view.find_by_selector("entity.other.inherited-class.cfml")
	if len(extends_regions) > 0:
		extends = view.substr(extends_regions[0])
		return extends.lower()
	return None
