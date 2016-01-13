# CFML Package for Sublime Text 3

This package provides CFML syntax highlighting as well as function and tag completions. It recognizes the following file extensions: `cfm,cfml,cfc`. Please see below for more of the features included in this package.

*Note: Please ensure that you are running at least the latest beta build of Sublime Text 3 (3083), as some of the features of the package will not work otherwise. If you are on the latest dev builds (3092+) the package will use the new `sublime-syntax` syntax highlighting.*

You can install this package via [Package Control](https://packagecontrol.io/). Please restart Sublime Text after installation.

Manual installation is also possible by downloading the repository and placing it in a folder within your Sublime packages folder. (See below for more information.)

### Acknowledgements

This package was developed from the following packages:

* https://github.com/SublimeText/ColdFusion
* https://github.com/sublimehq/Packages (especially the HTML and JavaScript syntaxes)
* https://github.com/Benvie/JavaScriptNext.tmLanguage (from which the current Sublime JavaScript syntax is derived)

Special thanks to [@foundeo](https://github.com/foundeo) and [cfdocs.org](http://cfdocs.org), from which this package gets its function and tag data. Also, thanks to [@mjhagen](https://github.com/mjhagen) who helped me get this package off the ground.

### Completions

Completions are included for tags and tag attributes, as well for built-in functions and member functions. Completions are also available for `Application.cfc` settings and methods.

In addition, there is the ability on a per project basis, via the `.sublime-project` file, to index folders of components, and then completions will be offered after typing a `.` if the preceding text matches a component file, or component file and containing directory (as DI/1 has it). So, for example, if a `services/user.cfc` file is found, then when typing either `user.` or `userService.`, the functions from that cfc will be offered as completions. To set this up you add the following setting to your project file: `"model_completion_folders":    [ "/full/path/to/model", "/another/full/path/to/index" ]`.

### Inline Documentation

<kbd>F1</kbd> is mapped to an inline documentation command that provides an inline documentation popup based on the cursor position.

*Note: You can always override the default key binding in your user key bindings file.*

If the documentation command is run when the cursor is within a built-in function or tag it will load the cfdocs.org documentation for that function or tag. Thus, having the cursor anywhere within `dateFormat(myDate, "yyyy-mm-dd")` and pressing <kbd>F1</kbd> (by default) will trigger a popup displaying the documentation for `dateFormat`. Similarly, having the cursor anywhere within `<cfinclude template="myOtherTemplate.cfm">` and pressing <kbd>F1</kbd> will trigger the display of the documention for `cfinclude`.

Inline documentation is also available for `Application.cfc` settings and methods as well as method calls that have been indexed via the model completions functionality (see above). In the latter case documentation of the function signature, file location, and argument list is provided.

### Package Settings

There are a number of package settings that control the behavior of the package. You can see the default settings from the menu under `Package Settings -> CFML -> Package Settings - Default` or via the command palette: `CFML: Default Package Settings`. To override any of these settings, use the user package settings file. This can be found under the menu `Package Settings -> CFML -> Package Settings - User` or via the command palette: `CFML: User Package Settings`. These settings control much of the functionality of the package mentioned in what follows.

### Key Bindings

In tag attributes, script strings, and between `cfoutput` tags, pressing `#` when text is selected will wrap the currently selected text `#selected#`.

<kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>D</kbd> will output a `<cfdump>` tag or `writeDump()/dump()` function in CFML script, wrapping any currently selected text.

<kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>O</kbd> will output a `<cfoutput>` tag or `writeOutput()` function in CFML script, wrapping any currently selected text.

<kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>A</kbd> will output a `<cfabort>` tag or `abort;` in CFML script.

If Sublime Text's `auto_close_tags` setting is true, when a closing tag's `/` has been pressed, the closing tag will be completed. There are two package settings that control which CFML and HTML tags should not be closed: `cfml_non_closing_tags` and `html_non_closing_tags`.

If the package setting `cfml_auto_insert_closing_tag` is set to `true` (by default it is `false`), when `>` is pressed in a tag, the corresponding closing tag will be automatically inserted after the cursor position. The package setting `cfml_non_closing_tags` controls which CFML tags will not get a closing tag auto inserted.

The package setting `cfml_between_tag_pair` controls the behavior of the editor when <kbd>ENTER</kbd> is pressed while the cursor is between a CFML tag pair (e.g. `<cfoutput>|</cfoutput>`). By default only a single new line is inserted. This can be changed to have an extra new line auto inserted between the tag pair (with an optional indent), and the cursor placed there. See the default settings for more information.

### Custom Coloring for CFML Tags

Unless you are using a specialized color scheme, CFML and HTML tags will receive the same coloring. This can make it a bit harder to distinguish between the two types of tags when embedding CFML tags in HTML. This package has a command you can run from the command palette that will inject custom colors for CFML tags into your current color scheme (or remove them if they are already there). Press <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd> to bring up the command palette (<kbd>CMD</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd> on a Mac) and run `CFML: Toggle Color Scheme Styles`. You can edit the styles that will be injected via the user settings for this package.

*Caveat:* This feature works by either overriding or modifying your active color scheme file. Because of this, it may not work well with other packages that also modify the active color scheme in some way. Also, if the package containing your active color scheme is updated, it is likely that you will need to toggle the custom tag coloring off and then on again to pick up any changes.

### Controller/View Toggle

CFML MVC frameworks typically have the convention that a `controllers` and a `views` folder are contained in the same parent directory, and that controller names and methods correspond to view folder and file names. <kbd>CTRL</kbd>+<kbd>F1</kbd> (<kbd>CMD</kbd>+<kbd>F1</kbd> on a Mac) is mapped to a toggle command that will jump the editor back and forth between a view file and the controller method that corresponds to it. The settings which determine which folder names are regarded as controller and view folders are contained in the package settings file. By default, `controllers` and `handlers` are treated as controller folders, and `views` as the views folder. Alternate folder names can be specifed in the user package settings file.

### CommandBox

CommandBox (https://www.ortussolutions.com/products/commandbox) has been added as the default CFML build system. This simply means that running the build command (<kbd>F7</kbd> on Windows) on a CFML file will run `box ${filename}` as a shell command in the directory of the file and output the result in a pane within Sublime Text (it can also be selected from the build system menu available via <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>B</kbd>). For this to work, CommandBox needs to be installed, and the CommandBox `box` binary needs to be available system wide, so that `box` can be run in any directory (see https://ortus.gitbooks.io/commandbox-documentation/content/setup/installation.html).

### TestBox

TestBox (https://www.ortussolutions.com/products/testbox) completions and inline documentation are available for `BaseSpec` components. They are enabled by default, but can be disabled globally by adding `"testbox_enabled": false` to your CFML user package settings, or on a per project basis by adding the same setting to a project settings file. The completions and documentation are offered in any cfc that is contained under a folder named `tests` (alternate folders can be specified in the settings), as well as in any cfc that extends `testbox.system.BaseSpec`.

There are three build system variants for running TestBox tests from within Sublime Text. The first is for running all of a project's tests, which can be used no matter what project files are open, so long as the active file is a CFML one. The next variant is for running all of the tests in the directory of the currently active file, while the last variant runs the tests in the currently active test cfc only. <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>B</kbd> calls up the build system menu, from which these options can be selected. Once one of the variants has been run, <kbd>CTRL</kbd>+<kbd>B</kbd> can used to run the last selected option again, without having to go through the menu.

Several settings need to be set in a project in order for these build systems to function. The first setting is `testbox_runner_url`, which should be the URL to a TestBox runner which runs tests and returns results in JSON. This needs to be setup so that a dot delimited directory of tests to run can be appended to it. An example URL that does this might be the following: `http://localhost:8888/testbox/system/Testbox.cfc?method=runremote&reporter=json&directory=`. The second setting is `testbox_default_directory`, which is the dot delimited directory that will be appended to the `testbox_runner_url` when the build variant for running all of a project's tests is selected. The last setting is `testbox_tests_root`, which is the root directory path that is used to determine the dot delimited path to a test directory when running the tests in a particular folder or file. (This could be the path to your project's webroot if your tests are contained under the webroot, but might not be if mappings are used.)

Results are displayed in a results pane. If there are errors or failures you can step backwards and forwards through the file stack traces via <kbd>F4</kbd> and <kbd>SHIFT</kbd>+<kbd>F4</kbd>. As each file is selected, Sublime Text opens that file and jumps to the line indicated. You can also double click on any file, and Sublime Text will open it for you.  Since the path to your files might look different to Sublime Text and the CFML application server (for example, if the server is running on a virtual machine), there is one more setting that maps the path as it appears to the server to the path as it appears to Sublime Text. Use `testbox_results.server_root` and `testbox_results.sublime_root` to specify the respective root paths to your project, so that Sublime Text can accurately open the files in stack traces.

All of the settings for TestBox can be seen in the default package settings.

### Framework One

Framework One (https://github.com/framework-one/fw1) function completions and `variables.framework` setting completions are available. They are disabled by default, but can be enabled globally by adding `"fw1_enabled": true` to your CFML user package settings, or on a per project basis by adding the same setting to a project settings file. (Project based settings will override global settings. The default package settings for Framework One can be viewed in the CFML default package settings file.) The completions are offered in `Application.cfc` as well as in Framework One controller, view and layout files. (The folder names can be specified in the settings.) In controllers, Framework One method completions are offered after typing `framework.` and `fw.`.

### Manual Installation

Locate your Sublime Text 3 packages directory. This can be easily done by opening the command palette in Sublime Text (<kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd> on Windows, <kbd>CMD</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd> on a Mac), and running `Preferences: Browse Packages`.

On Windows it will typically be something like this:
`C:\Users\Username\AppData\Roaming\Sublime Text 3\Packages\`

On a Mac it will be something like this:
`/Users/Username/Library/Application Support/Sublime Text 3/Packages/`

#### Via Git

Open Terminal or Command Prompt and cd into your packages directory, then run:

    git clone https://github.com/jcberquist/sublimetext-cfml.git ./CFML

The specified `./CFML` subdirectory is optional and if it is not included the package will be cloned into `sublimetext-cfml`.

That's it, restart Sublime Text 3 - if you want to update the code to match this repo, simply run the following inside the folder where you installed the package:

    git pull origin master

#### Via ZIP Download

Use the `Download ZIP` option to download a zip of the repository to your computer. Unzip this, and copy the repository folder into your Sublime Text packages directory. You can leave the folder name as is, or rename it (e.g. to `CFML`).
