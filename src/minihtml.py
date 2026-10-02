import sublime


def from_source_text(source_text, syntax, region=None):
    pass


def from_view(view, region=None):
    truncated = False
    if not region:
        region = sublime.Region(0, view.size())

    if region.size() > 5000:
        region.b = region.a + 5000
        truncated = True

    region = view.line(region)

    color_scheme = view.style()

    start_point = region.begin()
    scope_name = view.scope_name(start_point)
    style_dict = get_style_for_point(view, start_point)
    spans = []
    for pt in range(region.begin(), region.end() + 1):
        current_scope_name = view.scope_name(pt)
        if scope_name != current_scope_name:
            scope_name = current_scope_name
            style_dict_current = get_style_for_point(view, pt)
            if not match_style_dicts(style_dict, style_dict_current):
                span = {}
                span["style"] = style_dict
                span["text"] = view.substr(sublime.Region(start_point, pt))
                spans.append(span)
                start_point = pt
                style_dict = style_dict_current
    if start_point != pt:
        span = {}
        span["style"] = style_dict
        span["text"] = view.substr(sublime.Region(start_point, pt))
        spans.append(span)

    styles = {}
    style_map = {}
    minihtml = ""
    for span in spans:
        span_html = render_span(span, styles, style_map)
        minihtml += span_html

    minihtml = '<div class="minihtml-container">' + minihtml
    if truncated:
        minihtml += "<br><strong>truncated...</strong>"
    minihtml += "</div>"
    css = render_css(color_scheme["foreground"], color_scheme["background"], styles)

    return css, minihtml


def render_css(foreground, background, styles):
    css = "<style>"
    css += ".minihtml-container{" + "color:" + foreground + ";"
    css += "background-color:" + background + ";"
    css += "font-size:0.9em;margin: 0;padding: 4px;}"
    for key in styles:
        css += "." + key + "{" + styles[key] + "}"
    css += "</style>"
    return css


def text_to_html(text):
    html = text.replace("&", "&amp;")
    html = html.replace("<", "&lt;")
    html = html.replace(">", "&gt;")
    html = html.replace("\n", "<br>")
    html = html.replace("  ", "&nbsp;&nbsp;")
    html = html.replace("\t", "&nbsp;&nbsp;")
    return html


def render_span(span, styles, style_map):
    span_html = text_to_html(span["text"])

    if span["style"]:
        start_span = '<span class="'
        span_classes = []
        for key in ["foreground", "background"]:
            if key in span["style"]:
                css_class_name = get_classname(
                    key, span["style"][key], styles, style_map
                )
                span_classes.append(css_class_name)
        start_span += " ".join(span_classes) + '">'

        if span["style"]["italic"]:
            span_html = "<em>" + span_html + "</em>"

        if span["style"]["bold"]:
            span_html = "<strong>" + span_html + "</strong>"

        span_html = start_span + span_html + "</span>"

    return span_html


def get_classname(key, color, styles, style_map):
    map_key = key[0] + "-" + color[1:]
    if map_key not in style_map:
        next_class_name = "_" + str(len(style_map))
        style_map[map_key] = next_class_name
        styles[next_class_name] = "color:" if key[0] == "f" else "background-color:"
        styles[next_class_name] += color + ";"
    return style_map[map_key]


def get_style_for_point(view, pt):
    return view.style_for_scope(view.scope_name(pt))


def match_style_dicts(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if len(a) != len(b):
        return False
    for key in a:
        if key not in b or a[key] != b[key]:
            return False

    return True


def get_selector_style_map(view, selectors):
    return {s: view.style_for_scope(s) for s in selectors}
