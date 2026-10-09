"""
Tests that run inside Sublime Text, with the UnitTesting package (see
test_context_type.py). The two commands behind `/` and `>` in a tag.
"""

import sublime
from unittesting import ViewTestCase

CFML = 'Packages/CFML/syntaxes/CFML.sublime-syntax'
PACKAGE_SETTINGS = 'cfml_package.sublime-settings'


class CloseTagTests(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view.assign_syntax(CFML)

    def typed(self, source):
        # the caret after source, as if it had just been typed
        self.setText(source)
        self.setCaretTo(0, len(source))

    def test_slash_closes_the_open_tag(self):
        self.typed('<cfif x><')
        self.view.run_command('cfml_close_tag')
        self.assertViewContentsEqual('<cfif x></cfif>')

    def test_slash_closes_the_innermost_open_tag(self):
        self.typed('<cfif x><cfloop index="i" from="1" to="2"><')
        self.view.run_command('cfml_close_tag')
        self.assertViewContentsEqual(
            '<cfif x><cfloop index="i" from="1" to="2"></cfloop>'
        )

    def test_a_closed_tag_is_not_closed_again(self):
        self.typed('<cfif x><cfset y = 1></cfif><')
        self.view.run_command('cfml_close_tag')
        self.assertViewContentsEqual('<cfif x><cfset y = 1></cfif></')

    def test_slash_with_no_open_tag_is_a_slash(self):
        self.typed('x<')
        self.view.run_command('cfml_close_tag')
        self.assertViewContentsEqual('x</')


class AutoInsertClosingTagTests(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view.assign_syntax(CFML)
        self.settings = sublime.load_settings(PACKAGE_SETTINGS)
        self.had_setting = self.settings.has('cfml_auto_insert_closing_tag')
        self.old_setting = self.settings.get('cfml_auto_insert_closing_tag')
        self.settings.set('cfml_auto_insert_closing_tag', True)

    def tearDown(self):
        if self.had_setting:
            self.settings.set('cfml_auto_insert_closing_tag', self.old_setting)
        else:
            self.settings.erase('cfml_auto_insert_closing_tag')
        super().tearDown()

    def typed(self, source):
        self.setText(source)
        self.setCaretTo(0, len(source))

    def test_the_closing_tag_is_inserted_after_the_caret(self):
        self.typed('<cfif x')
        self.view.run_command('cfml_auto_insert_closing_tag')
        self.assertViewContentsEqual('<cfif x></cfif>')
        self.assertCaretAt(0, len('<cfif x>'))

    def test_a_tag_without_a_closing_tag_is_only_ended(self):
        self.typed('<cfset x = 1')
        self.view.run_command('cfml_auto_insert_closing_tag')
        self.assertViewContentsEqual('<cfset x = 1>')

    def test_an_existing_closing_tag_is_kept(self):
        self.setText('<cfif x</cfif>')
        self.setCaretTo(0, len('<cfif x'))
        self.view.run_command('cfml_auto_insert_closing_tag')
        self.assertViewContentsEqual('<cfif x></cfif>')

    def test_off_by_default_the_tag_is_only_ended(self):
        self.settings.set('cfml_auto_insert_closing_tag', False)
        self.typed('<cfif x')
        self.view.run_command('cfml_auto_insert_closing_tag')
        self.assertViewContentsEqual('<cfif x>')
