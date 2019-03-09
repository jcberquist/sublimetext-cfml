from . import cfml_plugins
from . import completions
from . import component_index
from . import custom_tag_index
from . import events
from . import goto_cfml_file
from . import inline_documentation
from . import method_preview
from . import utils
from . import commands
from . import formatting

command_list = []


def _plugin_loaded():
    for k, v in globals().items():
        try:
            if "_plugin_loaded" in v.__dict__:
                v._plugin_loaded()
        except Exception:
            pass


# load commands
for k in dir():
    try:
        v = globals()[k]
        for a in dir(v):
            if a.endswith("Command"):
                command_list.append(v.__dict__[a])
    except Exception:
        pass
