import json
import pathlib
import re

def wrap_regex(regex, indent=8):
    return re.sub(r"(.{80}[^|]*)", r"\1\n%s" % (" " * indent), regex)


def generate_function_regex():
    functions = pathlib.Path(
        "../src/plugins_/basecompletions/json/cfml_functions.json"
    ).read_text()
    keys = [k.lower() for k in json.loads(functions)]
    prefixes = [
        'array',
        'struct',
        'component',
        'cache',
        'entity',
        'image',
        'date',
        'transaction',
        'xml',
        'spreadsheet',
        'orm',
        'object',
        'list',
        'query',
        'create',
        'get',
        'url',
        'is',
        'store',
        'to',
        'replace',
    ]

    prefixed = {}
    non_prefixed = []

    for item in sorted(keys):
        for prefix in prefixes:
            if item.startswith(prefix) and len(item) > len(prefix):
                prefixed.setdefault(prefix, []).append(item[len(prefix) :])
                break
        else:
            non_prefixed.append(item)

    func_list = []

    for prefix in sorted(prefixed):
        string = prefix + "(?:" + "|".join(prefixed[prefix]) + ")"
        func_list.append(string)

    func_list.extend(non_prefixed)

    return wrap_regex("|".join(func_list))


def generate_member_function_regex():

    member_functions = set()

    data = pathlib.Path(
        "../src/plugins_/basecompletions/json/cfml_member_functions.json"
    ).read_text()
    data = json.loads(data)
    

    for member_type in data:
        methods = [m.lower() for m in data[member_type].keys()]
        member_functions.update(methods)

    return wrap_regex("|".join(sorted(list(member_functions))))


def generate_tag_regex():
    tags_to_filter = [
        'abort',
        'admin',
        'case',
        'catch',
        'component',
        'continue',
        'defaultcase',
        'else',
        'elseif',
        'exit',
        'finally',
        'function',
        'if',
        'interface',
        'print',
        'rethrow',
        'retry',
        'return',
        'script',
        'servlet',
        'servletparam',
        'set',
        'sleep',
        'switch',
        'try',
        'while',
    ]
    tags = pathlib.Path(
        "../src/plugins_/basecompletions/json/cfml_tags.json"
    ).read_text()
    tags = [t.lower()[2:] for t in json.loads(tags).keys() if t.lower()[2:] not in tags_to_filter]
    return wrap_regex("|".join(sorted(tags)))

support_functions = generate_function_regex()
member_functions = generate_member_function_regex()
tags_in_script = generate_tag_regex()

syntax = f"""
%YAML 1.2
---
name: CFScript (CFML) Base
scope: source.cfml.script.base
version: 2
hidden: true

variables:
  support_functions: |-
    (?x)(?i)
      (?:
        {support_functions}
      )

  member_functions: |-
    (?x)(?i)
      (?:
        {member_functions}
      )

  tags_in_script: |-
    (?x)(?i)
      (?:
        {tags_in_script}
      )

contexts:
  main:
    - match: .
"""

pathlib.Path('CFScript (CFML) Base.sublime-syntax').write_text(syntax.lstrip())
