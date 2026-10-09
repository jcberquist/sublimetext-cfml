"""
Scope selectors matched the way Sublime Text matches them, for the tests to
check a selector against the scope names the syntaxes give a point, as
view.match_selector() does. Covers what the package's selectors use: paths
of scope names, `,` and `|` for either, `&` for both, `-` for but not, and
parentheses.
"""

import re

# the scope of script inside a CFML file and of a .cfs file, where the script
# is the whole file; scopes found in script follow either
CFML_SCRIPT = 'embedding.cfml source.cfml.script '
CFS_SCRIPT = 'source.cfml.script '
SCRIPT_SCOPES = [
    '',
    'variable.other.readwrite.cfml',
    'meta.function-call.support.cfml support.function.cfml',
    'meta.function-call.method.cfml meta.function-call.arguments.cfml',
    'meta.string.cfml string.quoted.double.cfml',
    'comment.line.double-slash.cfml',
    'meta.tag.script.cfml entity.name.tag.script.cfml',
]

TOKEN = re.compile(r'\s*(?:([(),|&-])|([A-Za-z0-9_][\w.+-]*))')


def tokenize(selector):
    tokens = []
    pos = 0
    selector = selector.strip()
    while pos < len(selector):
        match = TOKEN.match(selector, pos)
        if not match:
            raise ValueError(f'cannot read selector {selector!r} at {pos}')
        tokens.append(match.group(1) or ('name', match.group(2)))
        pos = match.end()
    return tokens


def name_matches(selector_name, scope_name):
    return scope_name == selector_name or scope_name.startswith(selector_name + '.')


def path_matches(path, scope_names):
    # each name of the path matches a later scope name than the one before
    i = 0
    for name in path:
        while i < len(scope_names) and not name_matches(name, scope_names[i]):
            i += 1
        if i == len(scope_names):
            return False
        i += 1
    return True


class Parser:
    def __init__(self, selector, scope_names):
        self.tokens = tokenize(selector)
        self.scope_names = scope_names

    def peek(self):
        return self.tokens[0] if self.tokens else None

    def either(self):
        result = self.both()
        while self.peek() in (',', '|'):
            self.tokens.pop(0)
            result = self.both() or result
        return result

    def both(self):
        result = self.term()
        while self.peek() in ('&', '-'):
            op = self.tokens.pop(0)
            other = self.term()
            result = result and (other if op == '&' else not other)
        return result

    def term(self):
        if self.peek() == '(':
            self.tokens.pop(0)
            result = self.either()
            if self.tokens.pop(0) != ')':
                raise ValueError('unbalanced parentheses')
            return result
        path = []
        while isinstance(self.peek(), tuple):
            path.append(self.tokens.pop(0)[1])
        if not path:
            raise ValueError(f'expected a scope name, found {self.peek()!r}')
        return path_matches(path, self.scope_names)


def matches(scope, selector):
    """Returns whether a scope, such as view.scope_name() gives, matches a selector."""
    parser = Parser(selector, scope.split())
    result = parser.either()
    if parser.tokens:
        raise ValueError(f'cannot read selector {selector!r}')
    return result
