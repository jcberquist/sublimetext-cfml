import re
from collections import namedtuple


component = r"""
(?:/\*\*((?:\*(?!/)|[^*])*)\*/\s+)?
(?:<cf)?
component\b
([^>{]*)
"""
component = re.compile(component, re.I | re.X | re.S)
Component = namedtuple('Component', 'docblock attributes')


script_function = r"""
(?:/\*\*((?:\*(?!/)|[^*])*)\*/\s+)?
(?:\b(private|package|public|remote|static|final|abstract)\s+)?
(?:\b(private|package|public|remote|static|final|abstract)\s+)?
(?:\b([A-Za-z0-9_\.$]+)\s+)?
function\s+
([_$a-zA-Z][$\w]*)\s*
(\((?:=\s*\{|[^{])*)\{
"""
script_function = re.compile(script_function, re.I | re.X | re.S)
ScriptFunction = namedtuple(
    'ScriptFunction',
    'docblock storage_slot_1 storage_slot_2 returntype name arguments'
)


script_argument = r"""
(?:^\(|,)\s*
(?:(required)\s+)?
(?:\b(\w+)\b\s+)?
(\b\w+\b)
(?:\s*=\s*(\{[^\}]*\}|\[[^\]]*\]|\([^\)]*\)|(?:[^,\)](?!\b\w+\s*=))+))?
([^,\)]*)?
"""
script_argument = re.compile(script_argument, re.I | re.X)
ScriptArgument = namedtuple(
    'ScriptArgument',
    'required type name default attributes'
)


attribute = r"""
\b(\w+)\b(?:\s*=\s*(?:(['"])(.*?)(\2)|([a-z0-9:.]+)))?
"""
attribute = re.compile(attribute, re.I | re.X | re.S)
Attribute = namedtuple('Attribute', 'key quote_start value quote_end unquoted_value')


docblock = r"""
\n\s*(?:\*\s*)?(?:@(\w+)(?:\.(\w+))?)?\s*(\S.*)
"""
docblock = re.compile(docblock, re.I | re.X)
Docblock = namedtuple('Dockblock', 'key subkey value')


strings = r"""
"[^"]*"|'[^']*'
"""
strings = re.compile(strings, re.X)


function_attributes = r"""
\)([^)]*)$
"""
function_attributes = re.compile(function_attributes, re.X | re.S)

function_block = r"""
<cffunction\b.*?</cffunction>
"""
function_block = re.compile(function_block, re.X | re.I | re.S)

function_start_tag = r"""
<cffunction([^>]*)>
"""
function_start_tag = re.compile(function_start_tag, re.X | re.I)

argument_tag = r"""
<cfargument([^>]*)>
"""
argument_tag = re.compile(argument_tag, re.X | re.I)

cfml_property = r"""
^\s*
(?:<cf)?
property\b
([^;>]*)
"""
cfml_property = re.compile(cfml_property, re.X | re.I | re.M)

property_type_name = r"""
\A[\s\n]*
(?!\b\w+\s*=)
(?:(\w+)\s+)?
\b(\w+)\b
"""
property_type_name = re.compile(property_type_name, re.X)
