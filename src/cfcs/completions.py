from ..completions import CompletionList
from . import cfcs

def get_dot_completions(view, prefix, position, info):
	if not info["project_name"] or len(info["dot_context"]) == 0:
		return None
	# check for known cfc name
	cfc_name, cfc_name_region = cfcs.search_dot_context_for_cfc(info["project_name"], info["dot_context"])
	if cfc_name:
		return CompletionList(cfcs.get_cfc_completions(info["project_name"], cfc_name), 1, True)

	# also check for getter being used to access property
	symbol = info["dot_context"][-1]
	if symbol.is_function and symbol.name.startswith("get"):
		if cfcs.has_cfc(info["project_name"], symbol.name[3:]):
			return CompletionList(cfcs.get_cfc_completions(info["project_name"], symbol.name[3:]), 1, True)

	return None
