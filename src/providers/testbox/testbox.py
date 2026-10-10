import sublime
from ... import kinds
from ... import minihtml
from ... import utils
from ...cfml_view import Documentation


# the color of the side of the docs, a hue of the color scheme
ACCENT: minihtml.Hue = 'purplish'


testbox = {'completions': {}, 'documentation': {}}


def load():
    global testbox

    completions_data = load_json_data('completions')
    for key in completions_data:
        cfc = key.split('.').pop().capitalize()
        if cfc == 'Basespec':
            cfc = 'BaseSpec'
        testbox['completions'][key] = [
            make_completion(comp_key, completions_data[key][comp_key], cfc)
            for comp_key in sorted(completions_data[key].keys())
        ]
        if key == 'expectation':
            negated_completions = [
                make_completion(
                    negate_string(comp_key),
                    negate_string(completions_data[key][comp_key]),
                    cfc,
                )
                for comp_key in sorted(completions_data[key].keys())
            ]
            testbox['completions'][key].extend(negated_completions)

    testbox['documentation'] = load_json_data('documentation')


def make_completion(comp_key, contents, cfc):
    # keys are "name():returntype"
    name, returntype = comp_key.split('():')
    return sublime.CompletionItem(
        name,
        returntype,
        contents,
        sublime.CompletionFormat.SNIPPET,
        kind=kinds.METHOD,
        details='TestBox ' + cfc,
    )


def load_json_data(filename):
    return utils.load_json_resource('src/providers/testbox/json/' + filename + '.json')


def negate_string(string_to_negate):
    return 'not' + string_to_negate[0].upper() + string_to_negate[1:]


def extends_testbox(cfml_view):
    if cfml_view.view_metadata['extends']:
        return cfml_view.view_metadata['extends'].lower() == 'testbox.system.basespec'
    return False


def is_testbox_file(cfml_view):
    if extends_testbox(cfml_view):
        return True

    if not cfml_view.file_name:
        return False

    for folder in utils.get_project_setting(cfml_view.view.window(), 'testbox_folders'):
        if '/' + folder in cfml_view.file_path:
            return True
    return False


def get_dot_completions(cfml_view):
    if not utils.get_project_setting(cfml_view.view.window(), 'testbox_enabled'):
        return None

    # expectations
    if (
        is_testbox_file(cfml_view)
        and len(cfml_view.dot_context) > 0
        and cfml_view.dot_context[-1].name == 'expect'
    ):
        return testbox['completions']['expectation']

    # assertions
    if (
        is_testbox_file(cfml_view)
        and len(cfml_view.dot_context) == 1
        and cfml_view.dot_context[-1].name == 'assert'
    ):
        return testbox['completions']['assertion']

    return None


def get_script_completions(cfml_view):
    if not utils.get_project_setting(cfml_view.view.window(), 'testbox_enabled'):
        return None

    if is_testbox_file(cfml_view) and cfml_view.view.match_selector(
        cfml_view.position, 'meta.class.body.cfml'
    ):
        return testbox['completions']['basespec']

    return None


def get_inline_documentation(cfml_view, doc_type):
    if not utils.get_project_setting(
        cfml_view.view.window(), 'testbox_enabled'
    ) or not is_testbox_file(cfml_view):
        return None

    if cfml_view.view.match_selector(
        cfml_view.position, 'meta.function-call.method.cfml'
    ):
        function_call = utils.get_function_call(cfml_view.view, cfml_view.position)
        if function_call is None:
            return None
        function_name, function_name_region, function_args_region = function_call
        region = sublime.Region(
            function_name_region.begin(), function_args_region.end()
        )
        if doc_type == 'hover_doc' and not function_name_region.contains(
            cfml_view.position
        ):
            return None
        if cfml_view.view.substr(function_name_region.begin() - 1) == '.':
            dot_context = cfml_view.get_dot_context(function_name_region.begin() - 1)
            if dot_context[-1].name == 'expect':
                if function_name in testbox['documentation']['expectation']:
                    doc = get_documentation(
                        function_name,
                        testbox['documentation']['expectation'][function_name],
                    )
                    return Documentation(
                        [dot_context[-1].name_region, region], doc, None, 2
                    )
                if (
                    len(function_name) > 3
                    and function_name[:3] == 'not'
                    and function_name[3:] in testbox['documentation']['expectation']
                ):
                    doc = testbox['documentation']['expectation'][function_name[3:]]
                    return Documentation(
                        [dot_context[-1].name_region, region],
                        get_documentation(function_name, doc, True),
                        None,
                        2,
                    )
            if (
                dot_context[-1].name == 'assert'
                and function_name in testbox['documentation']['assertion']
            ):
                doc = get_documentation(
                    function_name, testbox['documentation']['assertion'][function_name]
                )
                return Documentation(
                    [dot_context[-1].name_region, region], doc, None, 2
                )

    if cfml_view.view.match_selector(cfml_view.position, 'meta.function-call.cfml'):
        function_call = utils.get_function_call(cfml_view.view, cfml_view.position)
        if function_call is None:
            return None
        function_name, function_name_region, function_args_region = function_call
        region = sublime.Region(
            function_name_region.begin(), function_args_region.end()
        )
        if doc_type == 'hover_doc' and not function_name_region.contains(
            cfml_view.position
        ):
            return None
        if function_name in testbox['documentation']['basespec']:
            doc = get_documentation(
                function_name, testbox['documentation']['basespec'][function_name]
            )
            return Documentation([region], doc, None, 2)

    return None


def get_documentation(key, metadata, negated=False):
    testbox_doc = minihtml.Doc(ACCENT)
    testbox_doc.header = metadata['header']
    testbox_doc.body = metadata['body']
    testbox_doc.links = metadata['links']

    if negated:
        testbox_doc.header += ' (negated)'
    return testbox_doc
