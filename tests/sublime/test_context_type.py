"""
Tests that run inside Sublime Text, with the UnitTesting package: the
command palette's "UnitTesting: Test Package" with the package name CFML.
They are not part of the pytest suite or of CI.

CfmlView reads the scopes of a real view to decide what the position is:
in a tag, after a dot, in the attributes of a script tag, or in script.
"""

from unittesting import ViewTestCase

from CFML.src.cfml_view import CfmlView, ContextType

CFML = 'Packages/CFML/syntaxes/CFML.sublime-syntax'
CFSCRIPT = 'Packages/CFML/syntaxes/CFScript (CFML).sublime-syntax'


class ContextTypeTests(ViewTestCase):
    # setText inserts as if typed, and auto-indenting the line after
    # `<cfscript>` would move every position in source
    view_settings = dict(ViewTestCase.view_settings, auto_indent=False)

    def context(self, syntax, source):
        """
        The CfmlView at the | of source, with the word before it as the
        prefix being typed.
        """
        position = source.index('|')
        source = source.replace('|', '', 1)
        prefix = source[:position]
        prefix = prefix[len(prefix.rstrip('abcdefghijklmnopqrstuvwxyz')) :]
        self.view.assign_syntax(syntax)
        self.setText(source)
        self.setCaretTo(0, 0)
        return CfmlView(self.view, position, prefix)

    def test_a_tag_name(self):
        cfml_view = self.context(CFML, '<cf|')
        self.assertEqual(cfml_view.type, ContextType.TAG)
        self.assertEqual(cfml_view.tag_location, 'tag_name')

    def test_the_attributes_of_a_tag(self):
        cfml_view = self.context(CFML, '<cfhttp url="x" |>')
        self.assertEqual(cfml_view.type, ContextType.TAG_ATTRIBUTES)
        self.assertEqual(cfml_view.tag_name, 'cfhttp')
        self.assertEqual(cfml_view.tag_location, 'tag_attributes')
        self.assertFalse(cfml_view.tag_in_script)

    def test_an_attribute_name_being_typed(self):
        cfml_view = self.context(CFML, '<cfhttp ur|')
        self.assertEqual(cfml_view.type, ContextType.TAG_ATTRIBUTES)
        self.assertEqual(cfml_view.tag_name, 'cfhttp')
        self.assertEqual(cfml_view.tag_location, 'tag_attribute_name')
        self.assertEqual(cfml_view.tag_attribute_name, 'ur')

    def test_text_outside_a_tag_is_the_tag_context(self):
        cfml_view = self.context(CFML, '<p>hello |</p>')
        self.assertEqual(cfml_view.type, ContextType.TAG)
        self.assertIsNone(cfml_view.tag_location)

    def test_script_in_a_cfscript_block(self):
        cfml_view = self.context(CFML, '<cfscript>\nfoo|\n</cfscript>')
        self.assertEqual(cfml_view.type, ContextType.SCRIPT)

    def test_a_dot_in_a_cfscript_block(self):
        cfml_view = self.context(CFML, '<cfscript>\nx.|\n</cfscript>')
        self.assertEqual(cfml_view.type, ContextType.DOT)

    def test_a_member_being_typed_after_a_dot(self):
        cfml_view = self.context(CFML, '<cfscript>\nx.ab|\n</cfscript>')
        self.assertEqual(cfml_view.type, ContextType.DOT)
        self.assertEqual(cfml_view.prefix, 'ab')

    def test_a_dot_in_a_tag_expression(self):
        cfml_view = self.context(CFML, '<cfset x = y.| >')
        self.assertEqual(cfml_view.type, ContextType.DOT)

    def test_a_dot_right_before_the_end_of_a_tag(self):
        cfml_view = self.context(CFML, '<cfset x = y.|>')
        self.assertEqual(cfml_view.type, ContextType.DOT)

    def test_the_attributes_of_a_component(self):
        cfml_view = self.context(CFML, 'component | {\n}')
        self.assertEqual(cfml_view.type, ContextType.TAG_ATTRIBUTES)
        # script tags are named as their tag, for the attribute data
        self.assertEqual(cfml_view.tag_name, 'cfcomponent')
        self.assertTrue(cfml_view.tag_in_script)

    def test_the_attributes_of_a_component_before_its_body(self):
        cfml_view = self.context(CFML, 'component |{\n}')
        self.assertEqual(cfml_view.type, ContextType.TAG_ATTRIBUTES)
        self.assertEqual(cfml_view.tag_name, 'cfcomponent')

    def test_the_attributes_of_a_tag_in_script(self):
        cfml_view = self.context(CFML, '<cfscript>\nhttp url="x" |;\n</cfscript>')
        self.assertEqual(cfml_view.type, ContextType.TAG_ATTRIBUTES)
        # the tag name is given its cf prefix
        self.assertEqual(cfml_view.tag_name, 'cfhttp')
        self.assertTrue(cfml_view.tag_in_script)

    def test_a_cfs_file_is_script_throughout(self):
        cfml_view = self.context(CFSCRIPT, 'foo|')
        self.assertEqual(cfml_view.type, ContextType.SCRIPT)

    def test_a_dot_in_a_cfs_file(self):
        cfml_view = self.context(CFSCRIPT, 'x.|')
        self.assertEqual(cfml_view.type, ContextType.DOT)

    def test_a_tag_in_a_cfs_file_is_not_a_tag_context(self):
        # `<` starts no tag in script, so this is script with a stray `<`
        cfml_view = self.context(CFSCRIPT, 'x = 1 < |')
        self.assertEqual(cfml_view.type, ContextType.SCRIPT)
