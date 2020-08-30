import json
import time
import urllib.request
import urllib.error
import certifi
from collections import deque
from . import utils

CFDOCS_BASE_URL = "https://raw.githubusercontent.com/foundeo/cfdocs/master/data/en/"
CFDOCS_HTTP_ERROR_MESSAGE = """
<p>HTTP requests to GitHub seem to be failing at the moment. This means that
cfdocs.org documentation is not currently available.</p>
<p>To avoid seeing this error message on mouse hover you can set the `cfml_hover_docs`
setting to false in your user package settings.</p>
<p>Please note that it is possible to load cfdocs.org data from a local drive by cloning or
downloading the cfdocs.org repo (https://github.com/foundeo/cfdocs) and using the `cfdocs_path`
package setting to point to the data folder of the repository.</p>
"""

cfdocs_cache = {}
cfdocs_failed_requests = deque()


def get_cfdoc(function_or_tag):
    if utils.get_setting("cfdocs_path"):
        return load_cfdoc(function_or_tag)
    return fetch_cfdoc(function_or_tag)


def load_cfdoc(function_or_tag):
    global cfdocs_cache
    file_path = function_or_tag + ".json"
    if file_path not in cfdocs_cache:
        full_file_path = (
            utils.normalize_path(utils.get_setting("cfdocs_path")) + "/" + file_path
        )
        try:
            with open(full_file_path, "r", encoding="utf-8") as f:
                json_string = f.read()
        except Exception:
            data = {"error_message": "Unable to read " + function_or_tag + ".json"}
            return data, False
        try:
            data = json.loads(json_string)
        except ValueError as e:
            data = {
                "error_message": "Unable to decode "
                + function_or_tag
                + ".json<br>ValueError: "
                + str(e)
            }
            return data, False

        cfdocs_cache[file_path] = data

    return cfdocs_cache[file_path], True


def fetch_cfdoc(function_or_tag):
    global cfdocs_cache, cfdocs_failed_requests
    file_path = function_or_tag + ".json"

    if file_path not in cfdocs_cache:
        while (
            len(cfdocs_failed_requests)
            and int(time.time() - cfdocs_failed_requests[0]) > 1800
        ):
            cfdocs_failed_requests.popleft()

        if len(cfdocs_failed_requests) > 2:
            data = {"error_message": CFDOCS_HTTP_ERROR_MESSAGE}
            return data, False

        full_url = CFDOCS_BASE_URL + file_path
        try:
            json_string = urllib.request.urlopen(full_url, cafile=certifi.where()).read().decode("utf-8")
        except urllib.error.HTTPError as e:
            cfdocs_failed_requests.append(time.time())
            data = {
                "error_message": "Unable to fetch "
                + function_or_tag
                + ".json<br>"
                + str(e)
            }
            return data, False

        try:
            data = json.loads(json_string)
        except ValueError as e:
            data = {
                "error_message": "Unable to decode "
                + function_or_tag
                + ".json<br>ValueError: "
                + str(e)
            }
            return data, False

        cfdocs_cache[file_path] = data

    return cfdocs_cache[file_path], True
