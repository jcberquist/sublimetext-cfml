import sublime
import sublime_plugin
import os


def get_rule_dicts():
    dicts = {
        "cfml_tag_style": {
            "name": "cfml tag",
            "scope": ", ".join(
                [
                    "entity.name.tag.cfml",
                    "entity.name.tag.script.cfml",
                    "entity.name.tag.custom.cfml",
                    "entity.name.tag.extension.cfml",
                ]
            ),
        },
        "cfml_tag_attribute_style": {
            "name": "cfml tag attribute",
            "scope": "entity.other.attribute-name.cfml",
        },
    }
    return dicts


def get_cfml_rules(appearance):
    cfml_settings = sublime.load_settings("cfml_package.sublime-settings")
    style_dicts = get_rule_dicts()
    rules = []
    for style_setting_key in style_dicts:
        style_setting = cfml_settings.get(style_setting_key)
        # a style without "light" and "dark" keys applies to both
        if style_setting and ("light" in style_setting or "dark" in style_setting):
            style_setting = style_setting.get(appearance)
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


def get_file_name(color_scheme):
    base_name = os.path.splitext(os.path.basename(color_scheme))[0]
    return base_name + ".sublime-color-scheme"


def get_active_appearance():
    # whether the color scheme in use has a light or a dark background
    palette = sublime.ui_info().get("color_scheme", {}).get("palette", {})
    background = palette.get("background", "#000000")
    r, g, b = (int(background[i : i + 2], 16) for i in (1, 3, 5))
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return "light" if luminance > 0.5 else "dark"


def get_color_scheme_files():
    # the override file name and appearance for each color scheme to style
    preferences = sublime.load_settings("Preferences.sublime-settings")
    color_scheme = preferences.get("color_scheme")
    if color_scheme == "auto":
        # the scheme follows the OS appearance, so style both
        light = get_file_name(preferences.get("light_color_scheme"))
        dark = get_file_name(preferences.get("dark_color_scheme"))
        if light != dark:
            return {light: "light", dark: "dark"}
        color_scheme = light
    return {get_file_name(color_scheme): get_active_appearance()}


def toggle():
    cfml_rule_names = {rule["name"] for rule in get_rule_dicts().values()}
    appearances = get_color_scheme_files()
    user_color_schemes = {
        file_name: get_user_color_scheme("Packages/User/" + file_name)
        for file_name in appearances
    }
    has_cfml_rules = any(
        rule.get("name") in cfml_rule_names
        for user_color_scheme in user_color_schemes.values()
        for rule in user_color_scheme["rules"]
    )

    for file_name, user_color_scheme in user_color_schemes.items():
        user_color_scheme["rules"] = [
            row
            for row in user_color_scheme["rules"]
            if row.get("name") not in cfml_rule_names
        ]
        if not has_cfml_rules:
            user_color_scheme["rules"].extend(get_cfml_rules(appearances[file_name]))

        user_color_scheme_path = os.path.join(
            sublime.packages_path(), "User", file_name
        )
        with open(user_color_scheme_path, "w") as f:
            f.write(sublime.encode_value(user_color_scheme, True))

        if len(user_color_scheme.keys()) == 1 and len(user_color_scheme["rules"]) == 0:
            print("CFML: Packages/User/{} is now empty.".format(file_name))


class CfmlColorSchemeStylesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        toggle()
