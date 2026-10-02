import sublime


def from_view(view, region=None):
    truncated = False
    if not region:
        region = sublime.Region(0, view.size())

    if region.size() > 5000:
        region = sublime.Region(region.begin(), region.begin() + 5000)
        truncated = True

    region = view.line(region)

    minihtml = '<div class="minihtml-container">'
    minihtml += view.export_to_html(region, minihtml=True)
    if truncated:
        minihtml += "<br><strong>truncated...</strong>"
    minihtml += "</div>"

    return minihtml


def get_selector_style_map(view, selectors):
    return {s: view.style_for_scope(s) for s in selectors}
