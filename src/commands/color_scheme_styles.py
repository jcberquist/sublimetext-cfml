import sublime
import sublime_plugin
import os


def get_rule_dicts():
    dicts = {
        "cfml_tag_style": {
            "name": "cfml tag",
            "scope": "entity.name.tag.cfml, entity.name.tag.script.cfml",
        },
        "cfml_tag_attribute_style": {
            "name": "cfml tag attribute",
            "scope": "entity.other.attribute-name.cfml",
        },
    }
    return dicts


def get_cfml_rules():
    cfml_settings = sublime.load_settings("cfml_package.sublime-settings")
    style_dicts = get_rule_dicts()
    rules = []
    for style_setting_key in style_dicts:
        style_setting = cfml_settings.get(style_setting_key)
        if style_setting:
            settings_to_inject = {
                k: style_setting[k]
                for k in ["foreground", "font_style"]
                if k in style_setting
            }
            style_dicts[style_setting_key].update(settings_to_inject)
            rules.append(style_dicts[style_setting_key])
    return rules


def get_user_color_scheme(color_scheme_file):
    try:
        src_str = sublime.load_resource(color_scheme_file)
        user_color_scheme = sublime.decode_value(src_str)
        if "rules" not in user_color_scheme:
            user_color_scheme["rules"] = []
        return user_color_scheme
    except IOError:
        return {"rules": []}


def remove_file_if_exists(file_path):
    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except Exception:
            print("CFML: unable to remove file: " + file_path)
            return False
    return True


def toggle():
    preferences = sublime.load_settings("Preferences.sublime-settings")
    color_scheme = os.path.basename(preferences.get("color_scheme"))
    color_scheme_file = os.path.splitext(color_scheme)[0] + ".sublime-color-scheme"
    user_color_scheme = get_user_color_scheme("Packages/User/" + color_scheme_file)
    user_color_scheme_path = os.path.join(
        sublime.packages_path(), "User", color_scheme_file
    )

    non_cfml_rules = [
        row
        for row in user_color_scheme["rules"]
        if "scope" not in row or not row["scope"].endswith("cfml")
    ]
    has_cfml_rules = len(user_color_scheme["rules"]) > len(non_cfml_rules)

    if has_cfml_rules:
        user_color_scheme["rules"] = non_cfml_rules
    else:
        user_color_scheme["rules"].extend(get_cfml_rules())

    with open(user_color_scheme_path, "w") as f:
        f.write(sublime.encode_value(user_color_scheme, True))

    if len(user_color_scheme.keys()) == 1 and len(user_color_scheme["rules"]) == 0:
        print("CFML: Packages/User/{} is now empty.".format(color_scheme_file))


class CfmlColorSchemeStylesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        if int(sublime.version()) < 3176:
            sublime.error_message(
                "Color scheme customization is only available in Sublime Text builds >= 3176"
            )
            return
        toggle()
