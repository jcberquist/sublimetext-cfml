import sublime
import sublime_plugin
from . import color_scheme_styles

__all__ = ["CfmlColorSchemeStylesCommand"]


class CfmlColorSchemeStylesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        if int(sublime.version()) < 3176:
            sublime.error_message(
                "Color scheme customization is only available in Sublime Text builds >= 3176"
            )
            return
        color_scheme_styles.toggle()
