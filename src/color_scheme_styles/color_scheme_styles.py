import sublime
import os
import plistlib
import shutil


def get_style_dicts():
    dicts = {
        "cfml_tag_style": {"name": "cfml tag", "scope": "entity.name.tag.cfml, entity.name.tag.script.cfml", "settings": {}},
        "cfml_tag_attribute_style": {"name": "cfml tag attribute", "scope": "entity.other.attribute-name.cfml", "settings": {}}
    }
    return dicts


def get_style_settings():
    cfml_settings = sublime.load_settings("cfml_package.sublime-settings")
    style_dicts = get_style_dicts()
    styles = []
    for style_setting_key in style_dicts:
        style_setting = cfml_settings.get(style_setting_key)
        if style_setting:
            settings_to_inject = {k: style_setting[k] for k in ["foreground", "fontStyle"] if k in style_setting}
            style_dicts[style_setting_key]["settings"] = settings_to_inject
            styles.append(style_dicts[style_setting_key])
    return styles


def get_current_color_scheme_parts(current_color_scheme):
    current_color_scheme_parts = current_color_scheme.split("/")
    package_name = current_color_scheme_parts[1]
    theme_file = current_color_scheme_parts[-1]
    relative_path_to_theme_file = "/".join(current_color_scheme_parts[1:-1])
    return package_name, theme_file, relative_path_to_theme_file


def is_installed_package(package_name):
    installed_package_path = sublime.installed_packages_path().replace("\\","/") + "/" + package_name + ".sublime-package"
    return os.path.isfile(installed_package_path)


def create_directory_if_not_exists(directory_path):
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
        except:
            print("CFML: unable to create directory: " + directory_path)
            return False
    return True


def remove_directory_if_exists(directory_path):
    if os.path.exists(directory_path):
        try:
            shutil.rmtree(directory_path)
        except:
            print("CFML: unable to remove directory: " + directory_path)
            return False
    return True


def remove_file_if_exists(file_path):
    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except:
            print("CFML: unable to remove file: " + file_path)
            return False
    return True


def toggle():
    current_color_scheme = sublime.load_settings("Preferences.sublime-settings").get("color_scheme").replace("\\", "/")
    packages_path = sublime.packages_path().replace("\\", "/")
    cache_path = sublime.cache_path().replace("\\", "/")
    package_name, theme_file, relative_path_to_theme_file = get_current_color_scheme_parts(current_color_scheme)

    current_theme = plistlib.readPlistFromBytes(sublime.load_binary_resource(current_color_scheme))
    non_cfml_settings = [row for row in current_theme["settings"] if "scope" not in row or not row["scope"].endswith("cfml")]

    # if there are no cfml styles, then add them, else remove them (i.e. toggle)
    adding_styles = len(non_cfml_settings) == len(current_theme["settings"])
    if adding_styles:
        current_theme["settings"].extend(get_style_settings())
    else:
        current_theme["settings"] = non_cfml_settings

    if adding_styles or not is_installed_package(package_name):
        directory_exists = create_directory_if_not_exists(packages_path + "/" + relative_path_to_theme_file)
        if not directory_exists:
            return
        plistlib.writePlist(current_theme, packages_path + "/" + relative_path_to_theme_file + "/" + theme_file)
    else:
        remove_directory_if_exists(packages_path + "/" + package_name)
        remove_file_if_exists(cache_path + "/" + relative_path_to_theme_file + "/" + theme_file + ".cache")
