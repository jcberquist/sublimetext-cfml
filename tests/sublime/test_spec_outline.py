"""
Tests that run inside Sublime Text, with the UnitTesting package (see
test_context_type.py). The TestBox spec outline reads the describe/it
calls of a view from its scopes.
"""

from unittest import TestCase

import sublime

from CFML.src.providers.testbox.testbox_spec_outline import TestboxSpecOutlineCommand

CFML = 'Packages/CFML/syntaxes/CFML.sublime-syntax'
CFSCRIPT = 'Packages/CFML/syntaxes/CFScript (CFML).sublime-syntax'

SPEC = """component extends="testbox.system.BaseSpec" {
    function run() {
        describe("A suite", function() {
            it("does a thing", function() {
            });
            describe(title="Nested", body=function() {
                it("a nested thing", function() {
                });
            });
        });
    }
}
"""


class SpecOutlineTests(TestCase):
    # a file view rather than ViewTestCase's output panel, which has no
    # window for the command to show its quick panel in
    def setUp(self):
        self.window = sublime.active_window()
        self.view = self.window.new_file()
        self.view.set_scratch(True)

    def tearDown(self):
        # the command shows its outline in a quick panel
        self.window.run_command('hide_overlay')
        self.view.close()

    def outline(self, syntax, source):
        self.view.assign_syntax(syntax)
        self.view.run_command('append', {'characters': source})
        self.view.sel().clear()
        self.view.sel().add(0)
        command = TestboxSpecOutlineCommand(self.view)
        command.run(None)
        return command

    def test_the_outline_nests_the_specs(self):
        command = self.outline(CFML, SPEC)
        self.assertEqual(
            command.outline,
            [
                'describe: A suite',
                '    it: does a thing',
                '    describe: Nested',
                '        it: a nested thing',
            ],
        )

    def test_the_spec_nearest_the_caret_is_selected(self):
        command = self.outline(CFML, SPEC)
        self.assertEqual(command.selected_index[0], 0)
        self.view.sel().clear()
        self.view.sel().add(self.view.text_point(6, 20))
        command = TestboxSpecOutlineCommand(self.view)
        command.run(None)
        self.assertEqual(command.selected_index[0], 3)

    def test_a_cfs_file_is_outlined(self):
        source = (
            'describe("A suite", function() {\n    it("a thing", function() {});\n});\n'
        )
        command = self.outline(CFSCRIPT, source)
        self.assertEqual(command.outline, ['describe: A suite', 'it: a thing'])

    def test_other_calls_are_not_specs(self):
        command = self.outline(CFSCRIPT, 'writeOutput("A suite");\n')
        self.assertEqual(command.outline, [])
