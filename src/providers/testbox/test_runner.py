# thanks to the Default Package - Default/exec.py

import sublime
import sublime_plugin
import json
import os
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
from functools import partial
from typing import Any
from ... import utils

# seconds to wait for the runner's response; a test run can take minutes
RUNNER_TIMEOUT = 300

def result_template(reporter, name):
    return utils.load_template("testbox/" + reporter + "/" + name + ".txt")


class TestboxCommand(sublime_plugin.WindowCommand):
    def run(self, test_type="", kill=False, **kwargs):
        # Cancel Build calls the build target again with kill=True
        if kill:
            return

        project_file_name = self.window.project_file_name()
        project_file_dir = (
            utils.normalize_path(os.path.dirname(project_file_name))
            if project_file_name
            else None
        )
        test_directory = ""
        test_bundle = ""

        if test_type in ["directory", "cfc"]:
            # the tests of the active file's directory or bundle
            view = self.window.active_view()
            file_name = view.file_name() if view else None
            if not file_name:
                sublime.message_dialog(
                    "Save the file to run the TestBox tests of its directory or bundle."
                )
                return
            directory, filename, ext = self.get_path_parts(file_name)
            tests_root = self.get_tests_root(project_file_dir, directory)
            if not tests_root:
                sublime.message_dialog(
                    '"testbox.tests_root" is missing, cannot determine dotted path for directory.'
                )
                return
            if not directory.startswith(tests_root):
                print(
                    "CFML: TestBox tests root "
                    + tests_root
                    + " does not contain "
                    + directory
                )
                sublime.message_dialog(
                    '"testbox.tests_root" does not contain the file, cannot determine dotted path for directory.'
                )
                return
            test_directory = self.get_dotted_directory(tests_root, directory)

            if test_type == "cfc":
                if ext != "cfc":
                    sublime.message_dialog(
                        'Invalid file type, only "cfc" extension is valid for TestBox tests.'
                    )
                    return
                test_bundle = test_directory + "." + filename

        runner = self.get_setting("runner")

        if not runner:
            sublime.message_dialog(
                "No TestBox runner has been defined for this project."
            )
            return

        if isinstance(runner, str):
            self.setup_tests(
                project_file_dir,
                self.get_runner_url(runner, test_directory, test_bundle),
                test_bundle,
            )
        elif isinstance(runner, list):
            if len(runner) == 1:
                k, v = runner[0].popitem()
                runner_url = self.get_runner_url(v, test_directory, test_bundle)
                self.setup_tests(project_file_dir, runner_url, test_bundle)
            else:
                self.select_runner(
                    project_file_dir, runner, test_directory, test_bundle
                )

    def select_runner(self, project_file_dir, runner_url, test_directory, test_bundle):
        items = []
        for r in runner_url:
            for k in r:
                items.append([k, r[k]])

        def on_done(index):
            if index != -1:
                runner_url = self.get_runner_url(
                    items[index][1], test_directory, test_bundle
                )
                self.setup_tests(project_file_dir, runner_url, test_bundle)

        self.window.show_quick_panel(items, on_done)

    def setup_tests(self, project_file_dir, runner_url, test_bundle):
        if not hasattr(self, "output_view"):
            self.output_view = self.window.create_output_panel("testbox")

        testbox_results = self.get_testbox_results(project_file_dir)
        reporter = self.get_setting("reporter")

        self.output_view.settings().set(
            "result_file_regex",
            re.escape(testbox_results["server_root"]) + "([^\\s].*):([0-9]+)$",
        )
        self.output_view.settings().set(
            "result_base_dir", testbox_results["sublime_root"]
        )
        self.output_view.settings().set("word_wrap", True)
        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax(
            utils.package_resource_path("syntaxes/testbox.sublime-syntax")
        )

        # As per Default/exec.py
        # Call create_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.create_output_panel("testbox")

        self.window.run_command("show_panel", {"panel": "output.testbox"})
        self.output_view.run_command(
            "append",
            {
                "characters": result_template(reporter, "logo"),
                "force": True,
                "scroll_to_end": True,
            },
        )

        sublime.status_message("CFML: running TestBox tests")
        self.start_tests(runner_url, test_bundle, reporter, self.get_timeout())

    def start_tests(self, runner_url, test_bundle, reporter, timeout):
        # the request gets its own thread rather than set_timeout_async():
        # Sublime's async thread is shared by every plugin, and a test run
        # can take minutes; each run waits for the one before it, so results
        # are still shown in the order the runs were started
        previous_run = getattr(self, "test_run", None)
        self.test_run = threading.Thread(
            target=self.run_tests,
            args=(previous_run, runner_url, test_bundle, reporter, timeout),
            daemon=True,
        )
        self.test_run.start()

    def run_tests(self, previous_run, runner_url, test_bundle, reporter, timeout):
        if previous_run:
            previous_run.join()

        print("CFML: TestBox runner - " + runner_url)
        result_string = fetch_results(runner_url, test_bundle, reporter, timeout)
        sublime.set_timeout(partial(self.show_results, result_string))

    def show_results(self, result_string):
        self.output_view.run_command(
            "append",
            {"characters": result_string, "force": True, "scroll_to_end": False},
        )

    def get_timeout(self):
        timeout = self.get_setting("timeout")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            return RUNNER_TIMEOUT
        return timeout if timeout > 0 else RUNNER_TIMEOUT

    def get_setting(self, setting_key) -> Any:
        # search in project settings, then box.json in root project folders, finally in package settings
        # a window without a project or folders has no project data
        project_data: dict[str, Any] = self.window.project_data() or {}
        if setting_key in project_data.get("testbox", {}):
            return project_data["testbox"][setting_key]

        project_file_name = self.window.project_file_name()
        project_file_dir = os.path.dirname(project_file_name) if project_file_name else None
        for folder in project_data.get("folders", []):
            setting = self.get_box_json_setting(
                folder["path"], project_file_dir, setting_key
            )
            if setting:
                return setting

        return (utils.get_setting("testbox") or {}).get(setting_key, "")

    def get_box_json_setting(self, folder, project_file_dir, setting_key) -> Any:
        project_path = utils.normalize_path(folder, project_file_dir)

        for file_name in os.listdir(project_path):
            if file_name.lower() == "box.json":
                break
        else:
            return None

        try:
            with open(project_path + "/" + file_name, encoding="utf-8") as f:
                box_json = json.loads(f.read())
        except (OSError, ValueError):
            print("CFML: Unable to load box.json file in " + project_path)
            return None

        if "testbox" in box_json and setting_key in box_json["testbox"]:
            return box_json["testbox"][setting_key]

        return None

    def get_runner_url(self, runner_url, test_directory, test_bundle):
        split_url = urllib.parse.urlsplit(runner_url)
        qs = {"reporter": ["json"]}
        for k, v in urllib.parse.parse_qs(split_url.query, True).items():
            if k.lower() == "reporter":
                continue
            if k.lower() == "directory" and len(test_directory) > 0:
                continue
            if k.lower() == "testbundles" and len(test_bundle) > 0:
                continue
            qs[k] = v

        if len(test_directory) > 0:
            qs["directory"] = [test_directory]

        if len(test_bundle) > 0:
            qs["testBundles"] = [test_bundle]

        runner_tuple = (
            split_url.scheme,
            split_url.netloc,
            split_url.path,
            urllib.parse.urlencode(qs, True),
            split_url.fragment,
        )
        return urllib.parse.urlunsplit(runner_tuple)

    def get_testbox_results(self, project_file_dir):
        # a user's "testbox" setting replaces the default one, so "results"
        # or its keys may be missing
        testbox_results = self.get_setting("results") or {}
        for key in ["server_root", "sublime_root"]:
            testbox_results[key] = utils.normalize_path(
                testbox_results.get(key, ""), project_file_dir
            )
            if len(testbox_results[key]) > 0:
                testbox_results[key] += "/"

        return testbox_results

    def get_tests_root(self, project_file_dir, directory):
        """
        Returns the root the dotted path of a test directory starts from,
        with a trailing slash, or "" when there is none: the tests_root
        setting, relative to the project file, else the project file's
        directory, else the window folder that holds the directory.
        """
        tests_root = utils.normalize_path(
            self.get_setting("tests_root"), project_file_dir
        )
        if not tests_root:
            tests_root = next(
                (
                    folder
                    for folder in utils.get_window_folders(self.window)
                    if directory.startswith(folder + "/")
                ),
                "",
            )
        return tests_root + "/" if tests_root else ""

    def get_path_parts(self, file_name):
        normalized_file_name = file_name.replace("\\", "/")
        file_parts = normalized_file_name.split("/")
        directory = "/".join(file_parts[:-1]) + "/"
        file_and_ext = file_parts[-1].split(".")
        return directory, file_and_ext[0], file_and_ext[1]

    def get_dotted_directory(self, root, directory):
        return directory.replace(root, "").replace("/", ".")[:-1]


# result rendering


def fetch_results(runner_url, test_bundle, reporter, timeout):
    try:
        with urllib.request.urlopen(runner_url, timeout=timeout) as response:
            json_string = response.read().decode("utf-8")
        return render_result(json.loads(json_string), test_bundle, reporter)
    except Exception as e:
        # urlopen() raises a timeout while connecting as a URLError
        reason = e.reason if isinstance(e, urllib.error.URLError) else e
        if isinstance(reason, TimeoutError):
            return (
                "\nThe TestBox runner did not respond within "
                + str(timeout)
                + " seconds:\n"
                + runner_url
                + '\nThe "testbox.timeout" setting sets how many seconds to wait.'
            )
        result_string = "\nError when trying to fetch:\n" + runner_url
        result_string += (
            "\nPlease verify the URL is valid and returns the test results in JSON."
        )
        result_string += "\n" + str(e)
        return result_string


def render_result(result_data, test_bundle, reporter):
    # lowercase all the keys since we can't guarantee the casing coming from CFML
    # also convert floats to ints, since CFML might serialize ints to floats
    result_data = preprocess(result_data)
    padToLen = 7 if reporter == "compacttext" else 0
    result_string = utils.expand_variables(
        result_template(reporter, "results"), filter_stats_dict(result_data, padToLen)
    )

    for bundle in result_data["bundlestats"]:
        if len(test_bundle) and bundle["path"] != test_bundle:
            continue

        result_string += utils.expand_variables(
            result_template(reporter, "bundle"), filter_stats_dict(bundle)
        )

        if isinstance(bundle["globalexception"], dict):
            result_string += (
                utils.expand_variables(
                    result_template(reporter, "global_exception"),
                    filter_exception_dict(bundle["globalexception"]),
                )
                + "\n"
            )

        for suite in bundle["suitestats"]:
            result_string += gen_suite_report(bundle, suite, reporter)

    result_string += "\n" + result_template(reporter, "legend")
    return result_string


def preprocess(source) -> Any:
    if isinstance(source, dict):
        return {k.lower(): preprocess(source[k]) for k in source}
    if isinstance(source, list):
        return [preprocess(item) for item in source]
    if isinstance(source, float):
        return int(source)
    return source


def filter_stats_dict(source, padToLen=0):
    stat_keys = [
        "path",
        "totalduration",
        "totalbundles",
        "totalsuites",
        "totalspecs",
        "totalpass",
        "totalfail",
        "totalerror",
        "totalskipped",
    ]

    def paddedText(key, toLen):
        txt = str(source[key])
        if key == "totalduration":
            txt = txt + " ms"
        if toLen == 0 or len(txt) >= toLen:
            return txt
        return txt + " " * (toLen - len(txt))

    return {key: paddedText(key, padToLen) for key in stat_keys if key in source}


def filter_exception_dict(source):
    exception_keys = ["type", "message", "detail", "stacktrace"]
    return {key: str(source[key]) for key in exception_keys if key in source}


def get_status_bit(status):
    status_dict = {"Failed": "!", "Error": "X", "Skipped": "-"}
    if status in status_dict:
        return status_dict[status]
    return "P"


def build_stacktrace(stack, tabs):
    stacktrace = ""
    for row in stack:
        stacktrace += (
            tabs
            + "     "
            + row["template"].replace("\\", "/")
            + ":"
            + str(row["line"])
            + "\n"
        )
    return stacktrace


def gen_suite_report(bundleStats, suiteStats, reporter, level=0):
    if (
        reporter == "compacttext"
        and bundleStats["totalfail"] + bundleStats["totalerror"] == 0
    ):
        return ""

    tabs = "    " * level
    report = (
        tabs
        + "("
        + get_status_bit(suiteStats["status"])
        + ")"
        + suiteStats["name"]
        + "\n"
    )
    level += 1
    for spec in suiteStats["specstats"]:
        if reporter == "compacttext" and spec["status"] not in ["Failed", "Error"]:
            continue

        tabs = "    " * level
        report += (
            tabs
            + "("
            + get_status_bit(spec["status"])
            + ")"
            + spec["name"]
            + " ("
            + str(spec["totalduration"])
            + " ms)"
            + "\n"
        )

        if spec["status"] == "Failed":
            report += tabs + "  -> Failure: " + spec["failmessage"] + "\n"
            report += build_stacktrace(spec["failorigin"], tabs)

        if spec["status"] == "Error":
            report += tabs + "  -> Error: " + spec["error"]["message"] + "\n"
            if "tagcontext" in spec["error"]:
                report += build_stacktrace(spec["error"]["tagcontext"], tabs)

    for nestedSuite in suiteStats["suitestats"]:
        report += (
            gen_suite_report(bundleStats, nestedSuite, reporter, level + 1).strip()
            + "\n"
        )

    return report
