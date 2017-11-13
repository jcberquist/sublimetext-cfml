from functools import partial
from .. import utils, minihtml

SIDE_COLOR = 'color(var(--orangish) blend(var(--background) 60%))'


def get_documentation(view, tag_name, file_path, tag_info):
    custom_tag_doc = {'side_color': SIDE_COLOR, 'html': {}}
    custom_tag_doc['html']['links'] = []

    custom_tag_doc['html']['header'] = tag_name
    custom_tag_doc['html']['description'] = '<strong>path</strong>: <a class="plain-link" href="__go_to_customtag">' + file_path + '</a>'

    custom_tag_doc['html']['body'] = '<br>'
    custom_tag_doc['html']['body'] += '<strong>Closing tag:</strong> ' + ('true' if tag_info['has_end_tag'] else 'false') + '<br>'
    custom_tag_doc['html']['body'] += '<strong>Attributes:</strong> ' + ', '.join(tag_info['attributes'])

    callback = partial(on_navigate, view, file_path)
    return custom_tag_doc, callback


def on_navigate(view, file_path, href):
    view.window().open_file(file_path)
