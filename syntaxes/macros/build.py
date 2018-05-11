import os

import sublime
import sublime_plugin

from YAMLMacros.api import build
from YAMLMacros.src.output_panel import OutputPanel
from YAMLMacros.src.error_highlighter import ErrorHighlighter


# adapted from YAMLMacros - BuildYamlMacrosCommand
# not imported by default as CFML only requires YAMLMacros
# for syntax development - in order to use this CFML needs
# to be extracted into your `Packages` directory and YAMLMacros
# must be installed.
class BuildCfmlSyntaxesCommand(sublime_plugin.WindowCommand):

    def run(self):
        src_dir = 'Packages/CFML/syntaxes/src/'
        dest_dir = 'CFML/syntaxes/'
        files = [
            'cfscript.sublime-syntax.yaml-macros',
            'cfscript-in-tags.sublime-syntax.yaml-macros',
            'cfml.sublime-syntax.yaml-macros'
        ]

        error_stream = OutputPanel(self.window, 'YAMLMacros')
        error_highlighter = ErrorHighlighter(self.window, 'YAMLMacros')

        for filename in files:
            target_name, _ = os.path.splitext(filename)
            file_path = os.path.join(sublime.packages_path(), src_dir, filename)
            build(
                source_text=sublime.load_resource(src_dir + filename),
                destination_path=os.path.join(sublime.packages_path(), dest_dir, target_name),
                arguments={'file_path': file_path},
                error_stream=error_stream,
                error_highlighter=error_highlighter
            )
