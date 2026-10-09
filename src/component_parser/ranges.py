import re
import collections


RangeDefinition = collections.namedtuple('RangeDefinition', ['start', 'end', 'child_ranges', 'pop'])


BASE_RANGES = [
    'comma',
    'semicolon',
    'curly_brackets',
    'line_comment',
    'multiline_comment',
    'parentheses',
    'square_brackets',
    'string_double',
    'string_single',
    'tag_comment'
]


NON_SCRIPT_RANGES = [
    'line_comment',
    'multiline_comment',
    'string_double',
    'string_single',
    'tag_comment'
]


RangeDefinitions = {
    'attributes': RangeDefinition(r'(?=.)', r'\{', BASE_RANGES, 'first'),
    'cfscript': RangeDefinition(r'(?=.)', r'\Z', BASE_RANGES, 'first'),
    'comma': RangeDefinition(r',', r'(?=.)', [], 'first'),
    'curly_brackets':RangeDefinition( r'\{', r'\}', BASE_RANGES, 'first'),
    'escaped_double_quote': RangeDefinition(r'""', r'(?=.)', [], 'first'),
    'escaped_hash': RangeDefinition(r'##', r'(?=.)', [], 'first'),
    'escaped_single_quote': RangeDefinition(r"''", r'(?=.)', [], 'first'),
    'hash': RangeDefinition(r'#', r'#', BASE_RANGES, 'first'),
    'line_comment': RangeDefinition(r'//', r'\n', [], 'first'),
    'multiline_comment': RangeDefinition(r'/\*', r'\*/', [], 'first'),
    'non_script': RangeDefinition(r'(?=.)', r'\Z', NON_SCRIPT_RANGES, 'first'),
    'parentheses': RangeDefinition(r'\(', r'\)', BASE_RANGES, 'first'),
    'semicolon': RangeDefinition(r';', r'(?=.)', [], 'first'),
    'square_brackets': RangeDefinition(r'\[', r'\]', BASE_RANGES, 'first'),
    'string_double': RangeDefinition(r'"', r'"', ['escaped_hash', 'hash', 'escaped_double_quote'], 'last'),
    'string_single': RangeDefinition(r"'", r"'", ['escaped_hash', 'hash', 'escaped_single_quote'], 'last'),
    'tag_comment': RangeDefinition(r'<!---', r'--->', [], 'first'),
    # a file read as tags: the text between tags is not script, so the
    # apostrophe in `<cfmail>Don't reply</cfmail>` does not open a string,
    # and only a cfscript block has the strings and comments of script
    'tag_text': RangeDefinition(r'(?=.)', r'\Z', ['tag_comment', 'cfscript_tag'], 'first'),
    'cfscript_tag': RangeDefinition(r'(?i:<cfscript>)', r'(?i:</cfscript>)', NON_SCRIPT_RANGES, 'first'),
}


RangeRegex = {}

for name, rd in RangeDefinitions.items():
    RangeRegex[name] = {
        'start': re.compile(rd.start, re.S)
    }

    patterns = []
    for cr in rd.child_ranges:
        crd = RangeDefinitions[cr]
        patterns.append((cr, crd.start))
    if rd.pop == 'first':
        patterns.insert(0, ('pop', rd.end))
    else:
        patterns.append(('pop', rd.end))
    RangeRegex[name]['end'] = re.compile('|'.join('(?P<{}>{})'.format(*p) for p in patterns), re.S)


class Range:

    def __init__(self, name, start=None, end=None):
        self.name = name
        self.start = start
        self.end = end
        self.parent = None
        self.children = []

    def add_child(self, child_range):
        child_range.parent = self
        self.children.append(child_range)

    def depth(self):
        depth = 0
        cr = self
        while cr.parent:
            cr = cr.parent
            depth += 1
        return depth

    def is_in_range(self, pt, names=None):
        if names is None:
            names = RangeDefinitions[self.name].child_ranges

        if self.start > pt or self.end <= pt:
            return False

        if self.name in names:
            return True

        start_index = 0
        end_index = len(self.children) - 1

        while end_index - start_index > 20:
            mid_index = start_index + ((end_index - start_index) // 2)
            if self.children[mid_index].start > pt:
                end_index = mid_index
            else:
                start_index = mid_index

        for child_range in self.children[start_index:]:
            if child_range.start > pt:
                break
            if child_range.end <= pt:
                continue
            if child_range.is_in_range(pt, names):
                return True

        return False

    def range_at_pt(self, pt):
        if self.start > pt or self.end < pt:
            return None

        if self.start == pt:
            return self

        for child_range in self.children:
            r = child_range.range_at_pt(pt)
            if r:
                return r

        return None

    def deepest_range(self, pt):
        # a range ends before its end point, which the next one can start at
        if self.start > pt or self.end <= pt:
            return None

        for child_range in self.children:
            dr = child_range.deepest_range(pt)
            if dr:
                return dr

        return self

    def next_child_range(self, pt, names=None):
        if self.start > pt or self.end < pt:
            return None

        for child_range in self.children:
            if child_range.start >= pt:
                if names is None or child_range.name in names:
                    return child_range

        return None

    def __repr__(self):
        txt = '(' + self.name + ': '
        txt += 'start=' + str(self.start)
        txt += ', end=' + str(self.end)

        if len(self.children) > 0:
            txt += ', children=['
            for c in self.children:
                child_txt = str(c).replace('\n', '\n    ')
                txt += '\n    ' + child_txt
            txt += '\n]'
        txt += ')'
        return txt


class RangeWalker:

    def __init__(self, src_txt, pos=0, name='cfscript'):
        self.src_txt = src_txt
        self.pos = pos
        self.name = name

    def walk(self):
        opening_match = RangeRegex[self.name]['start'].match(self.src_txt, self.pos)

        if opening_match is None:
            return None

        range_to_walk = Range(self.name, self.pos)

        pos = opening_match.end()
        current_range = range_to_walk

        while current_range:
            next_match = RangeRegex[current_range.name]['end'].search(self.src_txt, pos)

            if next_match is None:
                current_range.end = len(self.src_txt)
                while current_range.parent:
                    current_range.parent.end = len(self.src_txt)
                    current_range = current_range.parent
                break

            name = next_match.lastgroup
            pos = next_match.end()

            if name == 'pop':
                current_range.end = pos
                current_range = current_range.parent
                continue

            child_range = Range(name, next_match.start(), next_match.end())
            current_range.add_child(child_range)
            current_range = child_range

        return range_to_walk


class TagText:
    # the comments of a file that is read as tags, and the strings and
    # comments of its cfscript blocks, which are only looked for when the
    # first tag is checked, as most components have no tags

    def __init__(self, src_txt):
        self.src_txt = src_txt
        self.range = None

    def contains(self, pt):
        if self.range is None:
            self.range = RangeWalker(self.src_txt, 0, 'tag_text').walk()
        return self.range is not None and self.range.is_in_range(pt, NON_SCRIPT_RANGES)


class ScriptText:
    # the strings and comments of a file that is read as script

    def __init__(self, cfscript_range):
        self.range = cfscript_range

    def contains(self, pt):
        return self.range is not None and self.range.is_in_range(pt, NON_SCRIPT_RANGES)
