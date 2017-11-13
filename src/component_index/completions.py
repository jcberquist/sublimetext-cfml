from collections import namedtuple
from .. import utils

CfcCompletion = namedtuple("CfcCompletion", "key hint content file_path accessor private")

# note that the completion tuples include 4 elements, so they will need to be modified before
# being returned by subscribers


def build(project_name, file_paths, get_extended_metadata_by_file_path):
    completions = {}
    for file_path in file_paths:
        extended_metadata = get_extended_metadata_by_file_path(project_name, file_path)
        completions[file_path] = build_file_completions(extended_metadata)
    return completions


def build_file_completions(extended_metadata):
    file_completions = {}
    for completion_type in ["basic", "required", "full"]:
        comps = {"constructor": None}
        comps["functions"] = make_completions(extended_metadata["functions"], extended_metadata["function_file_map"], completion_type)

        if "init" in extended_metadata["functions"]:
            constructor_meta = extended_metadata["functions"]["init"]
            constructor_loc = extended_metadata["function_file_map"]["init"]
            comps["constructor"] = make_completion(constructor_meta, constructor_loc, completion_type)

        file_completions[completion_type] = comps

    return file_completions


def make_completions(funct_meta, funct_cfcs, completion_type):
    return [make_completion(funct_meta[funct_key], funct_cfcs[funct_key], completion_type) for funct_key in sorted(funct_meta)]


def make_completion(funct, cfc_file_path, completion_type):
    key = funct["name"]
    hint = "method"
    if utils.get_setting("cfc_completion_names") == "full":
        key += "()"
        if funct["meta"]["returntype"]:
            key += ":" + funct["meta"]["returntype"]
        hint = cfc_file_path.split("/").pop().split(".")[0]

    return CfcCompletion(
        key,
        hint,
        funct["name"] + "(" + make_arguments_string(funct["meta"]["parameters"], completion_type) + ")",
        cfc_file_path,
        funct["implicit"],
        funct["meta"]["access"] == "private"
    )


def make_arguments_string(parameters, completion_type):
    index = 1
    delim = ""
    arguments_string = ""

    if completion_type == "basic":
        return arguments_string

    for argument_params in parameters:
        if not argument_params:
            continue
        if argument_params["required"] or index == 1:
            arguments_string += delim + "${" + str(index) + ":" + make_argument_string(argument_params, completion_type) + "}"
            index += 1
        elif completion_type == "required":
            break
        else:
            arguments_string += "${" + str(index) + ":, ${" + str(index + 1) + ":" + make_argument_string(argument_params, completion_type) + "}}"
            index += 2
        delim = ', '
    return arguments_string


def make_argument_string(argument_params, completion_type):
    if completion_type == "required":
        return argument_params["name"]

    argument_string = "required " if argument_params["required"] else ""
    if argument_params["type"]:
        argument_string += argument_params["type"] + " "
    argument_string += argument_params["name"]
    if argument_params["default"]:
        argument_string += "=" + argument_params["default"]
    return argument_string
