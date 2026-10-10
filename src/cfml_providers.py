from . import utils
from .component_index import component_index
from .providers import (
    applicationcfc,
    language,
    cfdocs,
    components,
    custom_tags,
    fw1,
    current_file,
    testbox,
)

# completions are offered in this order: with nothing typed after a dot
# Sublime keeps it, so a component's methods come before the built-in
# member functions; it also breaks ties in the priority of docs and goto
modules = [
    applicationcfc,
    components,
    language,
    cfdocs,
    custom_tags,
    fw1,
    current_file,
    testbox,
]

providers = [module.provider for module in modules]

# subscribed on import, not in _plugin_loaded(), which runs again when
# cfml_plugin.py is reloaded while this module stays cached; still before
# the project watcher's _plugin_loaded() adds the open projects
for provider in providers:
    if provider.component_index_listener:
        component_index.subscribe(provider.component_index_listener)


def _plugin_loaded():
    for module in modules:
        if module.provider.load:
            utils.call_reporting_failure(
                module.__name__ + '.provider.load()', module.provider.load
            )
