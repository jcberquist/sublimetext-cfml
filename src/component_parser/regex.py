import re
from collections import namedtuple


# a docblock can come before the modifiers of a script component
component = r"""
(?:/\*\*((?:\*(?!/)|[^*])*)\*/\s+)?
(?:\b(?:abstract|final)\s+)*
(
    (?:<cf)?
    component\b
)
((?:[^>{"']|"[^"]*"|'[^']*')*)
"""
component = re.compile(component, re.I | re.X | re.S)
Component = namedtuple('Component', 'script docblock attributes')


# the modifiers, the return type and the name are on the line of the function
# keyword, or the last word of a comment or statement on the line above is
# taken for a return type, and a comment that ends in "function" makes a
# function of the `if (` on the line below
script_function = r"""
(?:/\*\*((?:\*(?!/)|[^*])*)\*/\s+)?
((?:\b(?:private|package|public|remote|static|final|abstract)[ \t]+)*)
(?:\b([A-Za-z0-9_\.$]+(?:\[\])?)[ \t]+)?
((?:\b(?:private|package|public|remote|static|final|abstract)[ \t]+)*)
\bfunction[ \t]+
([_$a-zA-Z][$\w]*)\s*
(?=\()
"""
script_function = re.compile(script_function, re.I | re.X | re.S)
ScriptFunction = namedtuple(
    'ScriptFunction',
    'docblock modifiers_before returntype modifiers_after name parameters attributes'
)


# a name or a type can have a $ in it, which \b does not take for a word
# character, so the search finds the first word of the parameter instead;
# a rest parameter is `...names`, as ColdFusion 2021 and later write it,
# with no type, so the type is only looked for when there is no ...
script_parameter = r"""
(?:(required)\s+)?
(?:(\.\.\.)\s*)?
(?(2)|(?:([\w$]+(?:\.[\w$]+)*(?:\[\])?)\s+)?)
([\w$]+)
(?:\s*=\s*(?P<default>\{[^\}]*\}|\[[^\]]*\]|\([^\)]*\)|(?:(?!\b\w+\s*=).)+))?
(.*)?
"""
script_parameter = re.compile(script_parameter, re.I | re.S | re.X)
ScriptParameter = namedtuple(
    'ScriptParameter',
    'required rest type name default attributes'
)


parameter_pattern_start = r"""
\s*(?:required\s+)?(?=[{\[])
"""
parameter_pattern_start = re.compile(parameter_pattern_start, re.I | re.X)


# an unquoted value runs to whitespace or to what ends the attributes: the
# body of a script function, the end of a tag or a property, or a comma;
# a call in it, `cachedWithin=createTimeSpan(0,1,0,0)`, keeps its arguments
attribute = r"""
\b(\w+)\b(?:\s*=\s*(?:(['"])(.*?)(\2)|((?:[^\s"'{}/>;,()]|\([^()]*\))+)))?
"""
attribute = re.compile(attribute, re.I | re.X | re.S)
Attribute = namedtuple('Attribute', 'key quote_start value quote_end unquoted_value')


# a line of a docblock, which is matched on its own so that a blank line
# does not join the next one to it; the text of the first line starts right
# after the /**, so a docblock on one line is that line
docblock = r"""
\s*(?:\*\s*)?(?:@(\w+)(?:\.(\w+))?)?\s*(.*)
"""
docblock = re.compile(docblock, re.I | re.X)
Docblock = namedtuple('Dockblock', 'key subkey value')


# a tag ends at a > that is not in a quoted attribute value
function_start_tag = r"""
<cffunction((?:[^>"']|"[^"]*"|'[^']*')*)>
"""
function_start_tag = re.compile(function_start_tag, re.X | re.I)

function_end_tag = r"""
</cffunction\s*>
"""
function_end_tag = re.compile(function_end_tag, re.X | re.I)

argument_tag = r"""
<cfargument((?:[^>"']|"[^"]*"|'[^']*')*)>
"""
argument_tag = re.compile(argument_tag, re.X | re.I)

# a property ends at a `;` or `>` that is not in a string, at a `//` comment,
# or at the end of a line when the next line does not go on with an attribute:
# with `name=` or with a name before the `;`. The line after a script property
# without a semicolon does neither.
cfml_property = r"""
^\s*
(?:<cf)?
property\b
(
    (?:
        [^;>\n"'/]+
        | "[^"]*"
        | '[^']*'
        | /(?!/)
        | \n[ \t]*(?=\w+\s*[=;])
    )*
)
"""
cfml_property = re.compile(cfml_property, re.X | re.I | re.M)

property_type_name = r"""
\A[\s\n]*
(?![\w$]+\s*=)
(?:([\w$]+(?:\.[\w$]+)*)\s+)?
([\w$]+)
"""
property_type_name = re.compile(property_type_name, re.X)
