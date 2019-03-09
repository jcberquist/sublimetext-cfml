from .custom_tags import CustomTags


custom_tag_index = CustomTags()


def _plugin_loaded():
    custom_tag_index.sync_projects()
