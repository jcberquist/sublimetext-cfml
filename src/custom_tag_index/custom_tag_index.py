import os
import re

attribute_regex = re.compile(r"\battributes\.(\w+)\b(?!\s*\()", re.I)
end_tag_regex = re.compile(
    r"thistag\.executionmode\s+(?:eq|is|==)\s+[\"']end[\"']", re.I
)
alt_end_tag_regex = re.compile(r"<cfcase\s+value=\s*[\"']end[\"']\s*>")


def index(custom_tag_path):
    custom_tags = {}
    for path, directories, filenames in os.walk(custom_tag_path):
        for filename in filenames:
            if filename.endswith(".cfm") or filename.endswith(".cfc"):
                full_file_path = path.replace("\\", "/") + "/" + filename
                file_index = index_file(full_file_path)
                if file_index:
                    custom_tags[full_file_path] = file_index
    return custom_tags


def index_file(full_file_path):
    try:
        with open(full_file_path, "r", encoding="utf-8") as f:
            file_string = f.read()
    except Exception:
        print("CFML: unable to read file - " + full_file_path)
        return None

    file_index = {"tag_name": full_file_path.split("/").pop()[:-4]}
    file_index.update(parse_cfm_file_string(file_string))
    return file_index


def parse_cfm_file_string(file_string):
    tag_index = {"has_end_tag": False}
    tag_index["attributes"] = list(
        sorted(set([attr.lower() for attr in re.findall(attribute_regex, file_string)]))
    )
    if re.search(end_tag_regex, file_string):
        tag_index["has_end_tag"] = True
    elif re.search(alt_end_tag_regex, file_string):
        tag_index["has_end_tag"] = True
    return tag_index
