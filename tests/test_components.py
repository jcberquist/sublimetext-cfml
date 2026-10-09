import types

import pytest

from CFML.src.cfml_view import ContextType
from CFML.src.component_reference import ComponentReference
from CFML.src.providers.components import (
    cfcs,
    components,
    dot_path_completions,
    entity_completions,
    provider,
    variable_names,
)
from CFML.src.utils import Symbol


class Region:
    def __init__(self, begin, end):
        self.a, self.b = begin, end

    def begin(self):
        return self.a

    def end(self):
        return self.b


# the view's position is on a variable at 10-21, which is an argument of a
# call at 0-30: `new Order(userService)`
POSITION = 12
NAME = Region(10, 21)
CALL = Region(0, 30)

# the methods of the components the fake finders find
METHODS = {'UserService': {'getuser'}, 'Legacy': set(), 'Order': {'getuser'}}


def reference(file_path, region=NAME, function_name='getuser'):
    return ComponentReference(file_path, file_path, function_name, [region])


def finder(found=None, completions=None):
    return components.Finder(
        lambda cfml_view: found,
        lambda cfml_view: found,
        lambda cfml_view: completions,
        lambda cfml_view, reference: ('doc', reference.file_path),
    )


def has_method(reference, function_name):
    return function_name in METHODS[reference.file_path]


@pytest.fixture(autouse=True)
def builders(monkeypatch):
    # stand-ins for the builders of component_reference, which read the
    # index: no method preview, goto or call doc for a method that the
    # component does not have, and goto to the component itself
    monkeypatch.setattr(
        components,
        'component_reference',
        types.SimpleNamespace(
            has_method=lambda cfml_view, reference: has_method(
                reference, reference.function_name
            ),
            get_method_preview=lambda cfml_view, reference: (
                ('preview', reference.file_path)
                if has_method(reference, reference.function_name)
                else None
            ),
            get_goto_cfml_file=lambda cfml_view, reference: (
                ('goto', reference.file_path)
                if not reference.function_name
                or has_method(reference, reference.function_name)
                else None
            ),
            get_completion_doc=lambda cfml_view, reference: (
                ('call doc', reference.file_path)
                if has_method(reference, cfml_view.function_call_params.function_name)
                else None
            ),
        ),
    )


def cfml_view(context_type=ContextType.DOT):
    return types.SimpleNamespace(
        type=context_type,
        project_name='site',
        position=POSITION,
        # a component with no properties
        view_metadata={'properties': {}},
        function_call_params=types.SimpleNamespace(
            function_name='getuser',
            dot_context=[types.SimpleNamespace(name_region=NAME)],
        ),
    )


def answers(view):
    return {
        'inline doc': provider.get_inline_documentation(view, 'inline_doc'),
        'method preview': provider.get_method_preview(view),
        'goto': provider.get_goto_cfml_file(view),
        'call doc': provider.get_completion_docs(view),
        'completions': provider.get_completions(view),
    }


def test_the_finders_are_asked_dot_paths_then_entities_then_variable_names():
    assert [finder.get_dot_completions for finder in components.FINDERS] == [
        dot_path_completions.get_dot_completions,
        entity_completions.get_dot_completions,
        variable_names.get_dot_completions,
    ]


def test_the_first_finder_with_an_answer_gives_it(monkeypatch):
    monkeypatch.setattr(
        components,
        'FINDERS',
        [
            finder(),
            finder(reference('Order'), ['order methods']),
            finder(reference('UserService'), ['user service methods']),
        ],
    )

    assert answers(cfml_view()) == {
        'inline doc': ('doc', 'Order'),
        'method preview': ('preview', 'Order'),
        'goto': ('goto', 'Order'),
        'call doc': ('call doc', 'Order'),
        'completions': ['order methods'],
    }


def test_the_next_finder_answers_what_the_first_has_no_answer_for(monkeypatch):
    # the variable is assigned a component that has no getUser(), and is a
    # cfc variable name for one that has
    monkeypatch.setattr(
        components,
        'FINDERS',
        [
            finder(reference('Legacy')),
            finder(),
            finder(reference('UserService'), ['user service methods']),
        ],
    )

    # the inline doc too, which the first would answer with its component's
    # doc: it is for the method that goto opens
    assert answers(cfml_view()) == {
        'inline doc': ('doc', 'UserService'),
        'method preview': ('preview', 'UserService'),
        'goto': ('goto', 'UserService'),
        'call doc': ('call doc', 'UserService'),
        'completions': ['user service methods'],
    }


def test_a_component_is_documented_when_no_finder_has_the_method(monkeypatch):
    monkeypatch.setattr(
        components,
        'FINDERS',
        [finder(reference('Legacy')), finder(), finder()],
    )
    view = cfml_view()
    assert provider.get_inline_documentation(view, 'inline_doc') == ('doc', 'Legacy')
    assert provider.get_goto_cfml_file(view) is None


def test_finders_that_find_the_same_method_give_one_answer(monkeypatch):
    # `variables.userService = new model.UserService()` in the file, where
    # userService is also a cfc variable name
    methods = ['getUser']
    monkeypatch.setattr(
        components,
        'FINDERS',
        [
            finder(reference('UserService'), methods),
            finder(),
            finder(reference('UserService'), methods),
        ],
    )

    view = cfml_view()
    assert provider.get_completions(view) == ['getUser']
    assert provider.get_inline_documentation(view, 'hover_doc') == (
        'doc',
        'UserService',
    )


def test_the_reference_closest_around_the_position_answers(monkeypatch):
    # dot paths find the component of the call around the variable, the
    # variable names the variable
    monkeypatch.setattr(
        components,
        'FINDERS',
        [
            finder(reference('Order', CALL, None)),
            finder(),
            finder(reference('UserService', NAME, None)),
        ],
    )
    view = cfml_view()
    assert provider.get_inline_documentation(view, 'hover_doc') == (
        'doc',
        'UserService',
    )
    assert provider.get_goto_cfml_file(view) == ('goto', 'UserService')


def test_a_call_doc_is_for_the_call_on_the_name_not_the_call_around_it(
    monkeypatch,
):
    # `new Order(userService.getUser(`, where Order also has a getUser()
    monkeypatch.setattr(
        components,
        'FINDERS',
        [
            finder(reference('Order', CALL, None)),
            finder(),
            finder(reference('UserService', NAME, None)),
        ],
    )

    assert provider.get_completion_docs(cfml_view()) == ('call doc', 'UserService')


def test_the_finders_are_asked_outside_a_project(monkeypatch):
    # a file opened alone can name a component next to it
    monkeypatch.setattr(components, 'FINDERS', [finder(reference('UserService'))])
    view = cfml_view()
    view.project_name = None

    assert provider.get_inline_documentation(view, 'inline_doc') == (
        'doc',
        'UserService',
    )
    assert provider.get_goto_cfml_file(view) == ('goto', 'UserService')
    assert provider.get_method_preview(view) == ('preview', 'UserService')
    assert provider.get_completion_docs(view) == ('call doc', 'UserService')


def test_script_completions_of_dot_paths_and_entities_are_both_offered(
    monkeypatch,
):
    view = cfml_view(ContextType.SCRIPT)
    monkeypatch.setattr(
        dot_path_completions, 'get_script_completions', lambda v: ['model.']
    )
    monkeypatch.setattr(entity_completions, 'get_script_completions', lambda v: None)
    assert provider.get_completions(view) == ['model.']

    monkeypatch.setattr(
        entity_completions, 'get_script_completions', lambda v: ['User']
    )
    assert provider.get_completions(view) == ['model.', 'User']

    monkeypatch.setattr(dot_path_completions, 'get_script_completions', lambda v: None)
    monkeypatch.setattr(entity_completions, 'get_script_completions', lambda v: None)
    assert provider.get_completions(view) is None


def test_the_index_listener_builds_the_data_of_each_finder(monkeypatch):
    built = []
    for module, name in [
        (cfcs, 'build_project_cfcs'),
        (dot_path_completions, 'build_project_map'),
        (entity_completions, 'build_project_entities'),
    ]:
        monkeypatch.setattr(
            module,
            name,
            lambda project_name, project_data, name=name: built.append(
                (name, project_name, project_data)
            ),
        )

    assert provider.component_index_listener
    provider.component_index_listener('site', None)
    assert built == [
        ('build_project_cfcs', 'site', None),
        ('build_project_map', 'site', None),
        ('build_project_entities', 'site', None),
    ]


def test_a_call_on_a_cfc_variable_name_covers_the_name(monkeypatch):
    monkeypatch.setattr(
        cfcs,
        'projects',
        {
            'site': {
                'userservice': [
                    cfcs.CfcInfo(
                        'UserService', '/site/model/UserService.cfc', True, False
                    )
                ]
            }
        },
    )
    # variables.userService.getUser(
    view = cfml_view()
    view.function_call_params.dot_context = [
        Symbol('userservice', False, None, None, NAME),
        Symbol('variables', False, None, None, Region(0, 9)),
    ]

    # the stand-in sublime.Region is a tuple
    found = variable_names.find_call_cfc(view)
    assert found == ComponentReference(
        '/site/model/UserService.cfc', 'UserService', None, [(10, 21)]
    )


def test_a_call_is_looked_up_on_one_name():
    # by dot paths and entities, which find a reference at any point
    found = []
    find = components.at_call(lambda view, position: found.append(position))
    view = cfml_view()
    find(view)
    assert found == [NAME.begin()]

    view.function_call_params.dot_context.append(
        types.SimpleNamespace(name_region=Region(0, 9))
    )
    assert find(view) is None
    assert found == [NAME.begin()]
