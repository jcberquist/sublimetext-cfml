import os, re

attribute_regex = re.compile("\\battributes\.(\w+)\\b", re.I)
end_tag_regex = re.compile("thistag\.executionmode\s+(?:eq|is|==)\s+[\"']end[\"']", re.I)
alt_end_tag_regex = re.compile("<cfcase\s+value=\s*[\"']end[\"']\s*>")

def index(custom_tag_path):
  custom_tags = {}
  for path in os.listdir(custom_tag_path):
    if path.endswith(".cfm") or path.endswith(".cfc"):
      full_file_path = custom_tag_path.replace("\\", "/") + '/' + path
      custom_tags[full_file_path] = index_file(full_file_path)
  return custom_tags

def index_file(full_file_path):
  try:
    with open(full_file_path, 'r') as f:
      file_string = f.read()
  except:
    print("CFML: unable to read file - " + full_file_path)
    return {}

  file_index = {"tag_name": full_file_path.split("/").pop()[:-4]}
  file_index.update(parse_cfm_file_string(file_string))
  return file_index

def parse_cfm_file_string(file_string):
  tag_index = {"has_end_tag": False}
  tag_index["attributes"] = list(sorted(set([attr.lower() for attr in re.findall(attribute_regex, file_string)])))
  if re.search(end_tag_regex, file_string):
    tag_index["has_end_tag"] = True
  elif re.search(alt_end_tag_regex, file_string):
    tag_index["has_end_tag"] = True
  return tag_index
