from scope_selectors import matches


def test_selectors_match_as_in_sublime_text():
    scope = 'embedding.cfml text.html.cfml meta.tag.cfml string.quoted.double.cfml'
    assert matches(scope, 'embedding.cfml')
    assert matches(scope, 'embedding meta.tag string')
    assert not matches(scope, 'meta.tag embedding.cfml')
    assert not matches(scope, 'meta.ta')
    assert not matches(scope, 'embedding.cfml - string.quoted')
    assert not matches(scope, 'embedding.cfml -string')
    assert matches(scope, 'source.cfml.script, meta.tag.cfml')
    assert matches(scope, 'source.cfml.script | meta.tag.cfml')
    assert not matches(scope, 'meta.tag.cfml & source.cfml.script')
    assert matches(
        scope,
        '(meta.tag.cfml, meta.tag.custom.cfml) - comment - (meta.tag.cfml comment)',
    )
    assert not matches(
        scope, '(meta.tag.cfml, meta.tag.custom.cfml) - (meta.tag.cfml string)'
    )
    assert matches('source.cfml.script meta.function-call.cfml', 'meta.function-call')
