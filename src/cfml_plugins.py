import importlib
from .plugins_.plugin import CFMLPlugin

directory = [
    "applicationcfc",
    "basecompletions",
    "cfcs",
    "cfdocs",
    "custom_tags",
    "dotpaths",
    "entities",
    "fw1",
    "in_file_completions",
    "testbox",
]

plugins = []


for p in directory:
    m = importlib.import_module(".plugins_." + p, __package__)
    globals()[p] = m
    for a in dir(m):
        v = m.__dict__[a]
        if a.endswith("Command"):
            globals()[a] = v
        elif a == "CFMLPlugin":
            try:
                if v.__bases__ and issubclass(v, CFMLPlugin):
                    plugins.append(v())
            except AttributeError:
                pass


def _plugin_loaded():
    for p in directory:
        m = globals()[p]
        if "_plugin_loaded" in m.__dict__:
            m._plugin_loaded()
