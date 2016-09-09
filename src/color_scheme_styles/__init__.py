import sublime_plugin
from os.path import dirname, realpath
from .color_scheme_styles import toggle

__all__ = ["CfmlColorSchemeStylesCommand"]
MODULE_PATH = dirname(realpath(__file__)).replace("\\", "/")


class CfmlColorSchemeStylesCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        toggle()
