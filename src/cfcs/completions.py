from ..completions import CompletionList
from . import cfcs

def get_dot_completions(view, prefix, position, info):
	if not info["project_name"] or len(info["dot_context"]) == 0:
		return None
	# check for known cfc name
	for symbol in info["dot_context"]:
		if not symbol.is_function:
			if cfcs.has_cfc(info["project_name"], symbol.name):
				return CompletionList(cfcs.get_cfc_completions(info["project_name"], symbol.name), 1, True)
			break
	# also check for getter being used to access property
	symbol = info["dot_context"][-1]
	if symbol.is_function and symbol.name.startswith("get"):
		if cfcs.has_cfc(info["project_name"], symbol.name[3:]):
			return CompletionList(cfcs.get_cfc_completions(info["project_name"], symbol.name[3:]), 1, True)

	return None
