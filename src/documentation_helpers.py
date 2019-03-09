CARD_TEMPLATE = """
<div class="card">
    <div class="card-header">{}</div>
    <div class="card-body">{}</div>
</div>
"""

HEADER_TEMPLATE = """
<strong>{key}{value}</strong>
"""


def header(key, value="", scope=""):
    args = {"key": key, "value": ""}
    if len(value):
        args["value"] = ": " + span_wrap(value, scope)
    return HEADER_TEMPLATE.format(**args)


def param_header(param):
    key = param["name"]
    value = param["type"] if "type" in param and param["type"] else ""
    html = header(key, value, "storage.type")

    if "required" in param and param["required"]:
        html += ' <span class="required">&nbsp;Required&nbsp;</span>'
    return html


def card(header="", body=""):
    html = CARD_TEMPLATE.format(header.strip(), body.strip())
    html = html.replace('<div class="card-header"></div>\n', "")
    if '<div class="card-body"></div>' in html:
        html = html.replace(
            '<div class="card-header">', '<div class="card-header card-header-empty">'
        )
        html = html.replace('<div class="card-body"></div>\n', "")
    return html


def span_wrap(txt, selector):
    return '<span class="' + selector.replace(".", "-") + '">' + txt + "</span>"


def clean_html(txt):
    return (
        txt.replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n ", "<br>")
        .replace("\n", "<br>")
    )
