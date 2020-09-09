import collections
import os
import re
import threading

import sublime
import sublime_plugin

import yamlmacros
import sublime_lib


SRC_DIR = "CFML/syntaxes/src/"
DEST_DIR = "CFML/syntaxes/"
FILES = [
    "cfscript.sublime-syntax.yaml-macros",
    "cfscript-in-tags.sublime-syntax.yaml-macros",
    "cfml.sublime-syntax.yaml-macros",
]

line_comment_re = re.compile(r"(^\s*#[^\n]*\n)\n+", re.MULTILINE)
dash_re = re.compile(r"^(\s*\-)\n+(\s*\-)", re.MULTILINE)
contexts_re = re.compile(r"^contexts:\n(.+)", re.DOTALL | re.MULTILINE)
context_re = re.compile(r"^  ([a-z\-]+):\n(?:(?!^  [a-z\-]+:)[^\n]*\n)+", re.MULTILINE)


def get_contexts(src):
    contexts_section = contexts_re.search(src)
    contexts = collections.OrderedDict()
    for context in context_re.finditer(src):
        if context.start() > contexts_section.start():
            contexts[context.group(1)] = context
    return contexts


def get_file_txt(file_dir, file_name):
    src_path = os.path.join(file_dir, file_name)
    with open(src_path) as f:
        src = f.read()
    return src_path, src


class BuildCfmlSyntaxesCommand(sublime_plugin.WindowCommand):
    """
    Adapted from YAMLMacros and Sublime-JS-Custom

    Not imported by default as CFML only requires YAMLMacros for syntax
    development - in order to use this CFML needs to be extracted into your
    `Packages` directory and dependencies on "yaml_macros_engine" and
    "sublime_lib" declared.
    """

    def run(self, src=None, dest=None):
        if src is None:
            src = os.path.join(sublime.packages_path(), SRC_DIR)
        if dest is None:
            dest = os.path.join(sublime.packages_path(), DEST_DIR)

        output = sublime_lib.OutputPanel.create(self.window, "YAMLMacros")
        output.show()

        def run():
            for file_name in FILES:
                target_name, _ = os.path.splitext(file_name)
                file_path, file_txt = get_file_txt(src, file_name)
                yamlmacros.build(
                    source_text=file_txt,
                    destination_path=os.path.join(dest, target_name),
                    arguments={"file_path": file_path},
                    error_stream=output,
                )

        threading.Thread(target=run).start()


class CleanCfmlSyntaxesCommand(sublime_plugin.WindowCommand):
    def run(self, src_dir=None):

        if src_dir is None:
            src_dir = os.path.join(sublime.packages_path(), DEST_DIR)

        for file_name in FILES:
            file_name = ".".join(file_name.split(".")[:-1])
            src_path, src_txt = get_file_txt(src_dir, file_name)

            if file_name == "cfscript-in-tags.sublime-syntax":
                src_txt = self.move_keys_to_top(
                    src_txt, ["variables", "hidden", "scope", "name"]
                )

            src_txt = self.clean_comments(src_txt)
            src_txt = self.clean_dashes(src_txt)
            src_txt = self.normalize_context_newlines(src_txt)

            with open(src_path, "w") as f:
                f.write(src_txt)

        self.order_contexts(
            src_dir, "cfscript.sublime-syntax", "cfscript-in-tags.sublime-syntax"
        )

    def move_keys_to_top(self, src_txt, keys):
        def move(s, m):
            top = re.search(r"^---\n", s, re.M)
            s = s[: m.start()] + s[m.end() :]
            s = s[: top.end()] + m.group() + s[top.end() :]
            return s

        for k in keys:
            m = re.search(r"^" + k + r":[^\n]*\n((?!\S)[^\n]*\n)*", src_txt, re.M)
            if m:
                src_txt = move(src_txt, m)

        return src_txt

    def clean_comments(self, src_txt):
        return line_comment_re.sub(r"\1", src_txt)

    def clean_dashes(self, src_txt):
        def clean(m):
            spacing = " " * (len(m.group(2)) - len(m.group(1)) - 1)
            return m.group(1) + spacing + m.group(2).lstrip()

        return dash_re.sub(clean, src_txt)

    def normalize_context_newlines(self, src_txt):
        contexts_section = contexts_re.search(src_txt)
        contexts = "\n\n".join(
            [v.group().rstrip() for k, v in get_contexts(src_txt).items()]
        )

        return src_txt[: contexts_section.start(1)] + contexts + "\n"

    def order_contexts(self, src_dir, src, target):
        src_path, src_txt = get_file_txt(src_dir, src)
        target_path, target_txt = get_file_txt(src_dir, target)
        src_contexts, target_contexts = get_contexts(src_txt), get_contexts(target_txt)

        ordered_contexts = collections.OrderedDict()
        for c in src_contexts:
            ordered_contexts[c] = target_contexts[c]
        for c in target_contexts:
            if c not in src_contexts:
                ordered_contexts[c] = target_contexts[c]
        ordered_contexts_txt = "".join([v.group() for k, v in ordered_contexts.items()])

        with open(target_path, "w") as f:
            contexts = contexts_re.search(target_txt)
            target_txt = target_txt[: contexts.start(1)] + ordered_contexts_txt
            f.write(target_txt)
