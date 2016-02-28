import re
from .. import model_index
from .. import utils

component_name_re = re.compile("[\"']component[\"']\s*,\s*(?:class\s*=\s*)?[\"']([$_\w.]+)[\"']", re.I)
cfc_dot_path_re = re.compile("^[\w\-_][\w.\-_]+$")

def get_component_name(source_string):
	cn = re.search(component_name_re, source_string)
	if cn:
		return cn.group(1)
	return None

def is_cfc_dot_path(source_string):
	dp = re.search(cfc_dot_path_re, source_string)
	if dp:
		return True
	return False

def get_folder_cfc_path(view, project_name, cfc_path):
	folder_mapping = get_folder_mapping(view, project_name)
	if folder_mapping:
		folder_cfc_path = folder_mapping
		if len(cfc_path) > 0:
			folder_cfc_path += "." + cfc_path
		return folder_cfc_path
	return None

def get_folder_mapping(view, project_name):
	"""
	Checks current file to see if it is inside of a mapped folder
	and returns the dot path to the file's containing folder.

	For example, if 'C:/projects/project/model/' is mapped to '/model',
	and the current file is 'C:/projects/project/model/services/myservice.cfc'
	then this function will return 'model.services'
	"""
	if not view.file_name():
		return None
	normalized_file_name = utils.normalize_path(view.file_name())
	mappings = model_index.get_project_data(project_name).get("mappings", [])
	for mapping in mappings:
		normalized_mapping = utils.normalize_mapping(mapping)
		if not normalized_file_name.startswith(normalized_mapping["path"]):
			continue
		mapped_path = normalized_mapping["mapping"] + normalized_file_name.replace(normalized_mapping["path"], "")
		path_parts = mapped_path.split("/")[1:-1]
		dot_path = ".".join(path_parts)
		if len(dot_path) > 0:
			return dot_path
	return None
