from CFML.src import kinds

from conftest import ROOT


def test_kinds_are_only_written_in_the_kinds_module():
    paths = sorted(ROOT.glob('cfml_plugin.py')) + sorted(ROOT.glob('src/**/*.py'))
    for path in paths:
        if path.name != 'kinds.py':
            assert 'KindId' not in path.read_text(encoding='utf-8'), path


def test_a_kind_has_a_letter_and_a_name():
    constants = [
        value
        for name, value in vars(kinds).items()
        if name.isupper() and isinstance(value, tuple)
    ]
    assert len(constants) > 5
    for _, letter, name in constants:
        assert len(letter) == 1 and letter.islower()
        assert name


def test_a_kind_is_named_for_what_it_completes():
    # and not for the package, or for the tag or function it belongs to
    assert kinds.TAG[2] == 'tag'
    assert kinds.ATTRIBUTE[1:] == ('a', 'attribute')
    assert kinds.VALUE[1:] == ('v', 'value')
    assert kinds.VARIABLE[1:] == ('v', 'variable')
    names = [value[2] for value in vars(kinds).values() if isinstance(value, tuple)]
    assert 'CFML' not in names
