from collections import namedtuple

CfcCompletion = namedtuple("CfcCompletion", "key content file_path accessor private")

# note that the completion tuples include 4 elements, so they will need to be modified before
# being returned by subscribers


def build(project_name, file_paths, get_extended_metadata_by_file_path):
    completions = {}
    for file_path in file_paths:
        extended_metadata = get_extended_metadata_by_file_path(project_name, file_path)
        completions[file_path] = build_file_completions(extended_metadata)
    return completions


def build_file_completions(extended_metadata):
    file_completions = {"constructor": None}
    if "init" in extended_metadata["functions"]:
        constructor_meta = extended_metadata["functions"]["init"]
        constructor_loc = extended_metadata["function_file_map"]["init"]
        file_completions["constructor"] = make_completion(constructor_meta, constructor_loc)
    file_completions["functions"] = make_completions(extended_metadata["functions"], extended_metadata["function_file_map"])
    return file_completions


def make_completions(funct_meta, funct_cfcs):
    return [make_completion(funct_meta[funct_key], funct_cfcs[funct_key]) for funct_key in sorted(funct_meta)]


def make_completion(funct, cfc_file_path):
    key_string = funct.name + "()"
    if funct.meta["returntype"]:
        key_string += ":" + funct.meta["returntype"]
    return CfcCompletion(
        key_string,
        funct.name + "(" + make_arguments_string(funct.meta["arguments"]) + ")",
        cfc_file_path,
        funct.implicit,
        funct.meta["access"] == "private"
    )


def make_arguments_string(arguments):
    index = 1
    delim = ""
    arguments_string = ""
    for argument_params in arguments:
        if not argument_params:
            continue
        if argument_params["required"] or index == 1:
            arguments_string += delim + "${" + str(index) + ":" + make_argument_string(argument_params) + "}"
            index += 1
        else:
            arguments_string += "${" + str(index) + ":, ${" + str(index + 1) + ":" + make_argument_string(argument_params) + "}}"
            index += 2
        delim = ', '
    return arguments_string


def make_argument_string(argument_params):
    argument_string = "required " if argument_params["required"] else ""
    if argument_params["type"]:
        argument_string += argument_params["type"] + " "
    argument_string += argument_params["name"]
    if argument_params["default"]:
        argument_string += "=" + argument_params["default"]
    return argument_string
