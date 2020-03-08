import sublime
import sublime_plugin
from HTML import html_completions
from .src import command_list, completions, events, utils, _plugin_loaded

for command in command_list:
    globals()[command.__name__] = command


def plugin_loaded():
    _plugin_loaded()


class CfmlEventListener(sublime_plugin.EventListener):
    def on_load_async(self, view):
        events.trigger("on_load_async", view)

    def on_close(self, view):
        events.trigger("on_close", view)

    def on_modified_async(self, view):
        events.trigger("on_modified_async", view)

    def on_post_save_async(self, view):
        if not view.file_name():
            print(
                "CFML: file was saved and closed - it is not possible to determine the file path."
            )
            return
        events.trigger("on_post_save_async", view)

    def on_post_text_command(self, view, command_name, args):
        if command_name == "commit_completion":
            pos = view.sel()[0].begin()

            if view.match_selector(
                pos,
                "meta.tag.cfml -source.cfml.script, meta.tag.script.cfml, meta.tag.script.cf.cfml, meta.class.declaration.cfml -meta.class.inheritance.cfml",
            ):
                if view.substr(pos - 1) in [" ", '"', "'", "="]:
                    view.run_command("auto_complete", {"api_completions_only": True})
                elif view.substr(pos) == '"':
                    # an attribute completion was most likely just inserted
                    # advance cursor past double quote character
                    view.run_command("move", {"by": "characters", "forward": True})

            if view.substr(pos - 1) == ":" and view.match_selector(
                pos - 1, "meta.tag.custom.cfml -source.cfml.script"
            ):
                view.run_command("auto_complete", {"api_completions_only": True})

            if view.substr(pos - 1) == "." and view.match_selector(
                pos - 1,
                "meta.function-call.support.createcomponent.cfml string.quoted, entity.other.inherited-class.cfml, meta.instance.constructor.cfml",
            ):
                view.run_command("auto_complete", {"api_completions_only": True})

    def on_post_window_command(self, window, command_name, args):
        events.trigger("on_post_window_command", window, command_name, args)

    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "embedding.cfml"):
            return None

        return completions.get_completions(view, locations[0], prefix)

    def on_hover(self, view, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT:
            return

        if not view.match_selector(point, "embedding.cfml"):
            return

        view.run_command(
            "cfml_inline_documentation", {"pt": point, "doc_type": "hover_doc"}
        )


class CustomHtmlTagCompletions(html_completions.HtmlTagCompletions):
    """
    There is no text.html scope in <cffunction> bodies, so this
    allows the HTML completions to still function there
    """

    def on_query_completions(self, view, prefix, locations):
        if not utils.get_setting("html_completions_in_tag_components"):
            return None

        # Only trigger within CFML tag component functions
        selector = "meta.class.body.tag.cfml meta.function.body.tag.cfml -source.cfml.script -source.sql"
        if not view.match_selector(locations[0], selector):
            return None

        # check if we are inside a tag
        is_inside_tag = view.match_selector(
            locations[0], "meta.tag - punctuation.definition.tag.begin"
        )

        return self.get_completions(view, prefix, locations, is_inside_tag)
