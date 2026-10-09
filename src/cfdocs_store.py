import json
import ssl
import sublime
import threading
import time
import urllib.request
from typing import Any
import certifi
from collections import deque
from . import utils

CFDOCS_BASE_URL = "https://raw.githubusercontent.com/foundeo/cfdocs/master/data/en/"
CFDOCS_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
CFDOCS_TIMEOUT = 10
# error messages are text, with a blank line between paragraphs
CFDOCS_HTTP_ERROR_MESSAGE = (
    "HTTP requests to GitHub seem to be failing at the moment. This means that"
    " cfdocs.org documentation is not currently available."
    "\n\n"
    "To avoid seeing this error message on mouse hover you can set the"
    " `cfml_hover_docs` setting to false in your user package settings."
    "\n\n"
    "Please note that it is possible to load cfdocs.org data from a local drive"
    " by cloning or downloading the cfdocs.org repo"
    " (https://github.com/foundeo/cfdocs) and using the `cfdocs_path` package"
    " setting to point to the data folder of the repository."
)

cfdocs_cache = {}
cfdocs_failed_requests = deque()
# fetches in progress, each with the callbacks to run when it finishes
cfdocs_pending = {}
# the error from a failed fetch, reported once by the next request
cfdocs_fetch_errors = {}
cfdocs_lock = threading.Lock()


def get_cfdoc(function_or_tag, on_loaded=None) -> tuple[dict[str, Any], bool] | None:
    """
    Returns a (data, success) tuple, or None while the doc is still being
    fetched from GitHub. In that case on_loaded, if given, is called on the
    main thread once the fetch has finished.
    """
    if utils.get_setting("cfdocs_path"):
        return load_cfdoc(function_or_tag)
    return fetch_cfdoc(function_or_tag, on_loaded)


def load_cfdoc(function_or_tag) -> tuple[dict[str, Any], bool]:
    global cfdocs_cache
    file_path = function_or_tag + ".json"
    if file_path not in cfdocs_cache:
        full_file_path = (
            utils.normalize_path(utils.get_setting("cfdocs_path")) + "/" + file_path
        )
        try:
            with open(full_file_path, encoding="utf-8") as f:
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
                + ".json\nValueError: "
                + str(e)
            }
            return data, False

        cfdocs_cache[file_path] = data

    return cfdocs_cache[file_path], True


def fetch_cfdoc(function_or_tag, on_loaded=None) -> tuple[dict[str, Any], bool] | None:
    file_path = function_or_tag + ".json"

    with cfdocs_lock:
        if file_path in cfdocs_cache:
            return cfdocs_cache[file_path], True

        if file_path in cfdocs_fetch_errors:
            return cfdocs_fetch_errors.pop(file_path), False

        while (
            len(cfdocs_failed_requests)
            and int(time.time() - cfdocs_failed_requests[0]) > 1800
        ):
            cfdocs_failed_requests.popleft()

        if len(cfdocs_failed_requests) > 2:
            data = {"error_message": CFDOCS_HTTP_ERROR_MESSAGE}
            return data, False

        if file_path not in cfdocs_pending:
            cfdocs_pending[file_path] = []
            thread = threading.Thread(
                target=fetch_in_background, args=(function_or_tag,), daemon=True
            )
            thread.start()
        if on_loaded:
            cfdocs_pending[file_path].append(on_loaded)

    return None


def fetch_in_background(function_or_tag):
    file_path = function_or_tag + ".json"
    data, success = request_cfdoc(function_or_tag)

    with cfdocs_lock:
        callbacks = cfdocs_pending.pop(file_path, [])
        if success:
            cfdocs_cache[file_path] = data
        elif callbacks:
            # kept for the refresh to show; otherwise the next request retries
            cfdocs_fetch_errors[file_path] = data

    for callback in callbacks:
        sublime.set_timeout(callback)


def request_cfdoc(function_or_tag):
    full_url = CFDOCS_BASE_URL + function_or_tag + ".json"
    try:
        with urllib.request.urlopen(
            full_url, timeout=CFDOCS_TIMEOUT, context=CFDOCS_SSL_CONTEXT
        ) as response:
            json_string = response.read().decode("utf-8")
    # URLError, HTTPError and timeouts are all OSErrors
    except OSError as e:
        with cfdocs_lock:
            cfdocs_failed_requests.append(time.time())
        data = {
            "error_message": "Unable to fetch " + function_or_tag + ".json\n" + str(e)
        }
        return data, False

    try:
        return json.loads(json_string), True
    except ValueError as e:
        data = {
            "error_message": "Unable to decode "
            + function_or_tag
            + ".json\nValueError: "
            + str(e)
        }
        return data, False
