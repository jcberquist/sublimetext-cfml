from . import cfml_providers
from . import component_index
from . import project_watcher
from . import utils
from . import view_state


def _plugin_loaded():
    for module in [
        component_index,
        cfml_providers,
        # last, so the indexes are set up before projects are added
        project_watcher,
    ]:
        utils.call_plugin_loaded(module)


def _plugin_unloaded():
    # a doc popup or method preview left in a view would outlive the
    # package, with links that no longer do anything
    view_state.close_all()
