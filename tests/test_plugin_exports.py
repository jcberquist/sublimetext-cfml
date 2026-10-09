import ast
from pathlib import Path

ROOT = Path(__file__).parent.parent


def sublime_plugin_classes(path):
    """the commands and listeners a module defines"""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            if (
                isinstance(base, ast.Attribute)
                and isinstance(base.value, ast.Name)
                and base.value.id == 'sublime_plugin'
            ):
                yield node.name


def test_every_command_and_listener_is_exported():
    # Sublime Text only registers the classes that cfml_plugin lists in its
    # __all__; one that is left out is never called, without any error
    plugin = ROOT / 'cfml_plugin.py'
    tree = ast.parse(plugin.read_text(encoding='utf-8'))
    exported = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign) and node.targets[0].id == '__all__'
    )

    defined = set()
    for path in [plugin, *sorted((ROOT / 'src').rglob('*.py'))]:
        defined.update(sublime_plugin_classes(path))

    assert defined
    assert defined - set(exported) == set()
