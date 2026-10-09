import types

from CFML.src.cfml_view import ContextType
from CFML.src.providers.provider import Provider


def view(context_type):
    return types.SimpleNamespace(type=context_type)


def test_completions_are_picked_by_the_context_type():
    provider = Provider(
        completions={
            ContextType.SCRIPT: lambda cfml_view: ['script'],
            ContextType.DOT: lambda cfml_view: ['dot'],
        }
    )

    assert provider.get_completions(view(ContextType.SCRIPT)) == ['script']
    assert provider.get_completions(view(ContextType.DOT)) == ['dot']


def test_no_completions_for_a_context_type_not_declared():
    provider = Provider(completions={ContextType.DOT: lambda cfml_view: ['dot']})

    assert provider.get_completions(view(ContextType.TAG)) is None
    assert provider.get_completions(view(None)) is None


def test_the_declared_functions_get_the_view():
    cfml_view = view(ContextType.SCRIPT)
    provider = Provider(
        completion_docs=lambda v: ('completion doc', v),
        goto_cfml_file=lambda v: ('goto', v),
        inline_documentation=lambda v, doc_type: (doc_type, v),
        method_preview=lambda v: ('preview', v),
    )

    assert provider.get_completion_docs(cfml_view) == ('completion doc', cfml_view)
    assert provider.get_goto_cfml_file(cfml_view) == ('goto', cfml_view)
    assert provider.get_inline_documentation(cfml_view, 'inline_doc') == (
        'inline_doc',
        cfml_view,
    )
    assert provider.get_method_preview(cfml_view) == ('preview', cfml_view)


def test_nothing_for_a_capability_not_declared():
    provider = Provider()
    cfml_view = view(ContextType.SCRIPT)

    assert provider.get_completions(cfml_view) is None
    assert provider.get_completion_docs(cfml_view) is None
    assert provider.get_goto_cfml_file(cfml_view) is None
    assert provider.get_inline_documentation(cfml_view, 'inline_doc') is None
    assert provider.get_method_preview(cfml_view) is None
