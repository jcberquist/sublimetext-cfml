# CFML Package for Sublime Text

This package provides CFML (ColdFusion Markup Language) support in Sublime Text.
It includes syntax highlighting, completions, and inline documentation, along
with the other features described below.

It supports components (`.cfc`), templates (`.cfm` and `.cfml`), and script
files (`.cfs`, as Lucee runs them). A `.cfs` file is script throughout, and gets
what the script in a component or template gets: completions, inline
documentation, the key bindings and commands, the build system, and formatting.
It is not a component, so it is not indexed, and the features for tags do not
apply to it.

You can install this package via
[Package Control](https://packages.sublimetext.com). The package name is
[CFML](https://packages.sublimetext.com/packages/CFML). Sublime Text should be
restarted after installation. Manual installation is also possible. See
[Installation](#installation) below.

## Table of Contents

- [Installation](#installation)
- [Settings](#settings)
- [Completions](#completions)
- [Inline Documentation](#inline-documentation)
- [Default Key Bindings](#default-key-bindings)
- [CFC Indexing and Dot Paths](#cfc-indexing-and-dot-paths)
- [Custom Tags](#custom-tags)
- [Code Formatting](#code-formatting)
- [Custom Coloring for CFML Tags](#custom-coloring-for-cfml-tags)
- [Controller/View Toggle](#controllerview-toggle)
- [CommandBox](#commandbox)
- [TestBox](#testbox)
- [Framework One](#framework-one)
- [Acknowledgements](#acknowledgements)

## Installation

The latest version of this package requires Sublime Text build 4213 or later. On
an earlier build, Package Control installs the newest tagged release that build
can run.

### Via Package Control

First ensure Package Control is installed. Recent versions of Sublime Text
include a menu item and a command palette entry for installing it. You can also
follow the instructions at <https://packages.sublimetext.com/installation>.

Open the command palette (<kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd> on
Windows and Linux, <kbd>CMD</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd> on a Mac) and
select `Package Control: Install Package`.

Wait for the list to open and find the `CFML` entry (subtitled with this
repository, `github.com/jcberquist/sublimetext-cfml`), then select it to
install.

Restart Sublime Text.

Package Control will keep the CFML package up to date automatically for you.

### Manual Installation

Locate your Sublime Text packages directory from the command palette with
`Preferences: Browse Packages`. It is typically:

    C:\Users\Username\AppData\Roaming\Sublime Text\Packages\

    /Users/Username/Library/Application Support/Sublime Text/Packages/

    ~/.config/sublime-text/Packages/

_Via Git_

`cd` into that directory and run:

    git clone https://github.com/jcberquist/sublimetext-cfml.git ./CFML

Restart Sublime Text.

To update the package later, run this inside the `CFML` folder:

    git pull origin master

_Via ZIP Download_

Use the `Download ZIP` option to download a zip of the repository to your
computer. (The master branch zip file is located at
<https://github.com/jcberquist/sublimetext-cfml/archive/master.zip>) Unzip this,
and copy the contents of the resulting repository folder into a subdirectory
named `CFML` in your Sublime Text packages directory.

Restart Sublime Text.

As changes are made to this repository and the package is updated you will need
to repeat this process (replacing the old contents in the `CFML` subdirectory)
in order to get your copy of the package up to date.

## Settings

There are several settings files that you should be aware of, as they control
much of the functionality of the package. Each one can be opened from the menu
or from the command palette (<kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd> on
Windows and Linux, <kbd>CMD</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd> on a Mac).

### Package Settings

You can access package settings from the menu under
`Package Settings -> CFML -> Settings` or via the command palette:
`CFML: Settings`. To override any of these settings, use the user package
settings file. (The default settings and user settings open side by side.)

### Syntax Settings

The package ships syntax-specific settings for the `CFML` syntax and for
`CFScript (CFML)`, the syntax used for script and for `.cfs` files. Those files
set `auto_complete_triggers`, which determine when Sublime Text offers
completions while you are typing. To change the triggers, or to set anything
else for only those files, open `Package Settings -> CFML -> Syntax Settings`
and `Package Settings -> CFML -> Script Syntax Settings`, or
`CFML: Syntax Settings` and `CFML: Script Syntax Settings` in the command
palette. These settings apply only to that specific syntax.

### Project Settings

Some settings are also (or only) able to be set on a per project basis. These
settings control the behavior of the package for a given project.

For example, component indexing (see
[CFC Indexing and Dot Paths](#cfc-indexing-and-dot-paths)),
[custom tags](#custom-tags) completions, and mappings are all configurable per
project.

You can access and edit project files from the menu under
`Project -> Edit Project` or via the command palette: `Project: Edit Project`.
(These will only be accessible after you have saved a project:
`Project -> Save Project As` or `Project: Save As`.)

### Bindings

The keyboard and mouse binding files are available in the menu under
`Package Settings -> CFML -> Key Bindings` and
`Package Settings -> CFML -> Mouse Bindings`. Or via the command palette at
`CFML: Key Bindings` and `CFML: Mouse Bindings`. The default and user files open
side by side.

## Completions

Completions are included for tags and tag attributes, as well as for built-in
functions and member functions. Completions are also available for
`Application.cfc` settings and methods.

Built-in function completions come in three styles, set by
`cfml_bif_completions`:

- `basic` inserts the function name only.
- `required`, the default, inserts the required arguments by name, without their
  types.
- `full` inserts every argument, including its type.

When entering a function call parameter for a built-in function, a pop-up window
with documentation from [cfdocs.org](http://cfdocs.org) for that parameter is
shown. This can be disabled by setting `cfml_completion_docs` to `false` in your
user package settings.

Member functions are offered after a period. As the type of the value is not
known, member function names are all listed once each, with the types the member
applies to shown beside the name, and their signatures in the details. Because
multiple signatures are possible, `cfml_bif_completions` does not apply to
member functions. Completions insert the name and empty parentheses.

Method completions from an indexed component use the same three styles, set by
`cfml_cfc_completions` (also `required` by default). After a period, a known
component's methods are listed before the built-in member functions. When the
name matches more than one component, the return type is replaced by a short
path that says which component the method comes from. See
[When a Name Could Be Several Components](#when-a-name-could-be-several-components).

While you fill in an argument of a built-in function or of an indexed component
method, a pop-up documents that argument. Set `cfml_completion_docs` to `false`
in your user package settings to turn these pop-ups off.

## Inline Documentation

<kbd>F1</kbd> opens an inline documentation pop-up for whatever is at the
cursor. The same command runs on hover. Hover docs are on by default, and can be
turned off by setting `cfml_hover_docs` to `false` in your user package
settings.

_The <kbd>F1</kbd> binding can be changed in your user key bindings._

Inside a built-in function or tag, the pop-up is the
[cfdocs.org](https://cfdocs.org) page for it. The cursor can be anywhere in
`dateFormat(myDate, "yyyy-mm-dd")` or in
`<cfinclude template="myOtherTemplate.cfm">`. The same documentation is
available for `Application.cfc` settings and methods.

If you have a copy of the cfdocs repository, set `cfdocs_path` to its data
directory (for example `"cfdocs_path": "C:/github/cfdocs/data/en/"`). The
documentation is then read from disk instead of being requested over HTTP.

## Default Key Bindings

In tag attributes, script strings, and between `cfoutput` tags, pressing `#`
with text selected wraps the selection as `#selected#`.

<kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>D</kbd>
(<kbd>CMD</kbd>+<kbd>ALT</kbd>+<kbd>D</kbd> on a Mac) inserts a `<cfdump>` tag
in a template, or a `writeDump()` call in script, wrapping any selected text.

<kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>O</kbd>
(<kbd>CMD</kbd>+<kbd>SHIFT</kbd>+<kbd>O</kbd> on a Mac) inserts a `<cfoutput>`
tag in a template, or a `writeOutput()` call in script, wrapping any selected
text.

<kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>A</kbd>
(<kbd>CMD</kbd>+<kbd>ALT</kbd>+<kbd>A</kbd> on a Mac) inserts a `<cfabort>` tag
in a template, or `abort;` in script.

<kbd>SHIFT</kbd>+<kbd>F1</kbd> shows the source of the component method at the
cursor, inline in the file. Press it again to close the preview.

When Sublime Text's `auto_close_tags` setting is `true`, typing `/` of a closing
tag completes the tag. `cfml_non_closing_tags` and `html_non_closing_tags` are
the CFML and HTML tags that are left unclosed.

When `cfml_auto_insert_closing_tag` is `true` (the default is `false`), typing
`>` in a tag inserts the closing tag after the cursor. `cfml_non_closing_tags`
controls which tags are excluded from this.

## CFC Indexing and Dot Paths

When you open a folder in Sublime Text, the package indexes the components
(CFCs) in it. The index is used to provides method completions, inline
documentation, argument pop-ups, and go to definition for variables that refer
to a component. It also completes and navigates dot paths, and a component's
completions and documentation include the properties and methods it inherits
through `extends`. The console (`View -> Show Console`) reports how many
component files were found in each folder.

A project file with `cfc_folders` and `mappings` set can be used to configure
this behavior more precisely for a specific project (though you can go far with
just the default behavior, you might find it desirable to have more targeted
indexing and completions in a given project). See
[Project Files](#project-files-cfc_folders-and-mappings) below for more.

### Which Files Are Indexed

In a folder that is a git work tree, the package asks git for the `.cfc` files
it does not ignore. Installed dependencies are usually ignored, so the package
also reads every `box.json` in the folder and indexes the `.cfc` files under the
folders named in its `installPaths`, each path resolved from the folder of that
`box.json`. That is how ColdBox, Framework One, and installed modules get
indexed. Folders whose names start with a dot, and `node_modules` folders, are
skipped. Files inside a git submodule are not indexed with the parent folder.

A folder that is not a git work tree, or any folder when git cannot be run, is
indexed only when one of these files is at its root: `box.json`, `server.json`,
`server-*.json`, `Application.cfc`, `Application.cfm`, or `.cfconfig.json`. Its
`.cfc` files are then found by walking the folder, again skipping folders whose
names start with a dot and `node_modules` folders. Opening your home folder does
not index it.

A folder with more component files than `cfml_index_max_files` (5,000 by
default) is not indexed. The same happens for a folder without git whose walk
would look at more than 100,000 files and folders.

Saving a `.cfc` file in Sublime Text indexes it when it is one of the files
described above, and saving a `box.json` indexes the folder again. Changes made
outside Sublime Text, such as `box install` or `git pull`, are picked up by
running `CFML: Index Active Project` from the command palette.

### Component Variables

By default, each indexed component is known by two variable names: its own name,
and its name followed by the name of its folder with a trailing "s" removed. So
`model/services/User.cfc` is known as `user` and `userService`, and
`handlers/Main.cfc` as `main` and `mainHandler`. These are the names DI/1 gives
to the beans it discovers, and the first is typically the name WireBox gives
them. Names are not case sensitive, and scope names (e.g. `application` or
`session`) are never used.

Typing one of these names and then a <kbd>.</kbd> offers the component's
methods. <kbd>F1</kbd>, the argument pop-ups, and
<kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>Left Click</kbd> work on the name and on its
method calls. They also work on a property of that name, which is how DI
frameworks inject a component. The match is made from the name alone, so the
documentation pop-up says "matched by name", and a variable that merely shares a
component's name is offered that component's methods too.

The mapping of components to variable names is configured by
`cfml_auto_variable_names`, which is a list of templates written the same way as
the `variable_names` of `cfc_folders` below. The default is
`["{cfc}", "{cfc}{cfc_folder_singularized}"]`. An empty list turns name matching
off.

**WireBox Injected Properties**

In a component, a property with an `inject` attribute is looked up by what the
attribute asks for, before it is looked up by its name. The component's own
properties and the ones it inherits are both checked.

```cfml
property name="jwt" inject="JWTService@cbsecurity";
property name="log" inject="logbox:logger:{this}";
property name="appName" inject="coldbox:setting:appName";
```

- A bean, as in the first line, is looked up as a variable name: `jwt` is the
  `JWTService` component, and then a component named `jwt`. The `@module` part
  is not used. An `id:`, `model:`, or `provider:` prefix is dropped, and an
  `inject` with no value means the property's own name.
- A ColdBox injection DSL, as in the second line, is the ColdBox class in the
  table below. The class is looked up by its full dot path, so ColdBox has to be
  indexed, which it is after `box install` has put it in the folder.
- Any other DSL, as in the third line, is not looked up. Matching it by the
  property's name would take a property named `log` to be a handler named
  `Log.cfc`.

| DSL                                                                                                                                                                                      | Class                                                                                        |
| :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------- |
| `coldbox`                                                                                                                                                                                | `coldbox.system.web.Controller`                                                              |
| `wirebox`                                                                                                                                                                                | `coldbox.system.ioc.Injector`                                                                |
| `logbox`                                                                                                                                                                                 | `coldbox.system.logging.LogBox`                                                              |
| `logbox:root`, `logbox:logger`, `logbox:logger:{name}`                                                                                                                                   | `coldbox.system.logging.Logger`                                                              |
| `cachebox`                                                                                                                                                                               | `coldbox.system.cache.CacheFactory`                                                          |
| `coldbox:handlerService`, `coldbox:interceptorService`, `coldbox:loaderService`, `coldbox:moduleService`, `coldbox:requestService`, `coldbox:routingService`, `coldbox:schedulerService` | `coldbox.system.web.services.` followed by the service name (`HandlerService`, and the rest) |
| `coldbox:renderer`                                                                                                                                                                       | `coldbox.system.web.Renderer`                                                                |
| `coldbox:flash`                                                                                                                                                                          | `coldbox.system.web.flash.AbstractFlashScope`                                                |
| `coldbox:asyncManager`                                                                                                                                                                   | `coldbox.system.async.AsyncManager`                                                          |
| `coldbox:router`                                                                                                                                                                         | `coldbox.system.web.routing.Router`                                                          |
| `coldbox:dataMarshaller`                                                                                                                                                                 | `coldbox.system.core.conversion.DataMarshaller`                                              |

### Dot Paths

Dot paths in the `extends` and `implements` attributes, in `createObject` where
the type is `component`, and after `new` (`new dot.path.to.component()`) are
resolved with no mappings required. The first rule that finds a component is the
one used:

1. Relative to the folder of the file the dot path is written in.
2. Through the `mappings` of the project file, when there is one.
3. From each folder of the window, as though it were the web root.
   `models.UserService` is `models/UserService.cfc` at the top of one of those
   folders.
4. Any indexed file whose path ends in the dot path.
   `cborm.models.VirtualEntityService` finds
   `modules/cborm/models/VirtualEntityService.cfc`, however deep `modules` is.
   Mappings are usually named after the folder they point at, which is why this
   finds most of what a mapping would. A single name found this way, as in
   `new Widget()`, is a guess. `new Query()` and CFML's other built-in
   components (`http`, `mail`, `ftp`, `storedproc`, `pdf`, `ldap`, `feed`) are
   not looked up this way.
5. For a dot path of more than one name, the file name alone. This is always a
   guess. It is what finds `framework.one` as `fw1/one.cfc` when the
   `/framework` mapping points at a folder named `fw1`, and it can also find a
   component that only shares the name.

The documentation pop-up says "matched by name" for a guess.

<kbd>F1</kbd> on a dot path opens a pop-up with the component's path, and with
its documentation when the component has been indexed. Click the path to open
the file. <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>Left Click</kbd> (on a Mac too)
jumps straight to the file. Both also work on a quoted string passed as a
function argument when the string is a dot path that resolves.

_The binding is in the default mouse bindings file. Add your own in the user
file. This one runs only in CFML files. A binding you add applies everywhere
unless you give it a context, so avoid overriding a Sublime Text mouse binding,
such as <kbd>CTRL</kbd>+<kbd>Left Click</kbd>, which adds a cursor._

`extends` is resolved the same way, so a component's documentation and
completions include the properties and methods it inherits. When a variable is
assigned an instantiated component (`myVar = new path.to.mycfc()`) and the dot
path resolves, a <kbd>.</kbd> after that variable offers the component's
methods, and <kbd>F1</kbd> and <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>Left
Click</kbd> work on the variable. You can set
`instantiated_component_completions` to `false` to turn this off.

Dot paths are themselves completed in `extends`, in `createObject`, and after
`new`. With the automatic index, the choices are the components and folders in
the file's own folder, at the root of each folder of the window, and under each
mapping. After a <kbd>.</kbd>, every folder whose path ends in what you have
typed is included, so `new models.` lists the components of every folder named
`models`. A project with `cfc_folders` offers the file's own folder and its
mappings, as described below.

### When a Name Could Be Several Components

A variable name or a dot path can match more than one component. Every match is
kept, best first:

1. Your own files come before files under a `box.json` install path.
2. Then the file that shares the most folders with the file you are in.
3. Then the file with the fewest folders in its path.
4. Then alphabetical order.

Files of the same name that the index reads as identical count once, since
nested dependencies often install the same package more than once. When a method
is called on the variable, only the components that have that method, including
inherited methods, are kept, unless none of them has it.

- Method completions after `name.` list the methods of every match. The
  annotation beside each one says which component it comes from, as the end of
  its path (`model/env`, `util/Env`).
- The documentation pop-up and the argument pop-ups use the first match, and the
  documentation pop-up links to the others after "also:".
- <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>Left Click</kbd> asks you to choose among
  the matches.

### Indexing Settings

| Setting                    | Default                                       | Meaning                                                                     |
| :------------------------- | :-------------------------------------------- | :-------------------------------------------------------------------------- |
| `cfml_auto_index`          | `true`                                        | Index the folders of the window, unless the project file has `cfc_folders`  |
| `cfml_auto_variable_names` | `["{cfc}", "{cfc}{cfc_folder_singularized}"]` | The variable names every indexed component is known by. `[]` turns this off |
| `cfml_index_max_files`     | `5000`                                        | The most component files a folder can have and still be indexed             |

You can override these in your user package settings, or for one project by
setting them at the top level of its project file. A change to the user package
settings is used the next time a project is indexed, so run
`CFML: Index Active Project` afterwards. _Note: None of these settings apply to
a project which has `cfc_folders` configured, since that setting overrides the
auto indexing behavior._

CFC indexing is cached, so a file is read again only when its contents change.
`CFML: Index Active Project` indexes the active project again from that cache.
`CFML: Clear Index Cache and Reindex` empties the cache first, so every CFC of
the open projects is read again.

### Project Files: `cfc_folders` and `mappings`

To choose the folders and the mappings for one project, set `cfc_folders` and
`mappings` in its project file. A real project file will have other settings
around these:

```json
{
  "mappings": [
    { "mapping": "/framework", "path": "C:/myprojects/projectname/framework" },
    { "mapping": "/model", "path": "C:/myprojects/projectname/app/model" }
  ],
  "cfc_folders": [
    {
      "path": "C:/myprojects/projectname/app/model",
      "variable_names": ["{cfc}", "{cfc}{cfc_folder_singularized}"],
      "accessors": false
    }
  ]
}
```

A path may be absolute, or relative to the project file.

When the project file has `cfc_folders`, only those folders are indexed and the
auto index settings above do not apply. Variable names come only from each
folder's `variable_names` templates, so a folder without that key will not have
its components matched to any variable names. An `inject` attribute is still
read: a bean is looked up among those names, and the class of a DSL is found
through `mappings`. Dot paths resolve only relative to the file and through
`mappings` (rules 1 and 2 above). A variable name given to more than one
component still offers all of them. `"cfc_folders": []` results in nothing being
indexed, whereas the key being absent from a project file keeps the automatic
index, and its `mappings` are used as rule 2.

`mappings` are also what `Copy CFC Dotted Path` uses. Right-click a CFC in the
sidebar and choose it. When more than one mapping matches, you are asked to pick
one. When none match, the project's base folder is the root of the dot path.

Each object in `cfc_folders` has one required key, `path`. That folder is
searched recursively for CFC files. `variable_names` is a list of templates, and
these placeholders are replaced:

| Key                         | Replacement                                               |
| :-------------------------- | :-------------------------------------------------------- |
| `{cfc}`                     | The component's name                                      |
| `{entity_name}`             | The component's entity name, or its name when it has none |
| `{cfc_folder}`              | The name of the folder that contains the component        |
| `{cfc_folder_singularized}` | That folder name with a trailing "s" removed              |

Any other text is kept, so a template can add a prefix or a suffix. A name can
contain periods, as in `application.services.{cfc}`. The resulting names work as
described in [Component Variables](#component-variables): a period after the
name offers the component's methods, and the documentation and goto commands
work on the name, on a property of that name, and on its method calls.

Implicit accessors are included unless `accessors` is set to `false`, in which
case only accessors written in the component are included. Without
`cfc_folders`, implicit accessors are always included.

When a component and the component it extends are both indexed, and the
`extends` path resolves relative to the child or through a mapping, the child's
documentation and completions include the parent's properties and methods.
Components that fall under a mapping are offered as dot path completions in
`extends`, in `createObject` where the type is `component`, and after `new`.

**Inject Property Command**

<kbd>SHIFT</kbd>+<kbd>ALT</kbd>+<kbd>D</kbd> inserts a property into a
component. On a component variable name or a call to one of its methods, the
property is named after that variable. Otherwise you get a list of the project's
component variable names and choose one. The templates are the `di_property`
settings. Override them in your user package settings, or in a project file.
After a property is inserted, the component's properties are sorted by name. Set
`sort_properties` to `false` inside `di_property` to leave them where they are.

## Custom Tags

Custom tags are configured per project, either with a `<cfimport>` prefix or in
the `<cf_customtag>` form. Other settings are left out of this example:

```json
{
  "custom_tag_folders": [
    {
      "path": "C:/myprojects/projectname/customtags/page",
      "prefix": "page"
    }
  ]
}
```

_**Note**: the path specified above can either be an absolute path, or a
relative path. If it is a relative path, it will be resolved relative to the
location of `.sublime-project` file._

Once this is done, `page` will be offered as a custom tag prefix completion, and
then after entering `<page:` a list of tags in the custom tag folder will be
offered. After a tag has been entered, completions for every `attributes` scope
variable found in that custom tag file will be offered.

**Important**: Alternatively, the `prefix` key can be omitted - in that case the
custom tags in that folder will be offered as `cf_tagname` completions.

You can use the <kbd>F1</kbd> documentation command to get some minimal
documentation about that custom tag, and
<kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>Left Click</kbd> can be used to jump to the
custom tag file.

The indexer will search for `thistag.executionmode is/eq/== "end"/'end'` (case
insensitive) or `<cfcase value="end"/'end'>` (case insensitive) in custom tag
files in order to determine whether or not to auto close the custom tag.

## Code Formatting

Files can be formatted by [cfformat](https://github.com/jcberquist/cfformat),
which must be installed separately. Once you have it on your system,
`CFML: Format File` in the command palette formats the current file. `cfformat`
finds its settings from the file's location, as it does on the command line. A
file that has never been saved is formatted as a component in the first folder
of the window. Anything cfformat could not format is left as written, and
reported in the status bar and the console.

A `cfformat` binary on your `PATH` is used by default. To use one somewhere
else, set `cfformat_path` (for example
`"cfformat_path": "C:/cfformat/cfformat.exe"`).

There is no key binding for formatting by default. To add one, put something
like this in your user key bindings:

```json
{
  "keys": ["alt+shift+f"],
  "command": "cfml_format",
  "context": [
    {
      "key": "selector",
      "operator": "equal",
      "operand": "embedding.cfml, source.cfml.script"
    }
  ]
}
```

## Custom Coloring for CFML Tags

In a typical color scheme, CFML and HTML tags will share a color. Run
`CFML: Toggle Color Scheme Styles` from the command palette to write a color
scheme customization
(<https://www.sublimetext.com/docs/color_schemes.html#customization>) into your
`Packages/User/` directory, so that CFML tags and tag attributes have their own
colors. Run the command again to remove what it added. When your Sublime Text
`color_scheme` is set to `"auto"`, both the light and the dark scheme are
customized. The colors come from `cfml_tag_style` and
`cfml_tag_attribute_style`, with a separate style for light and dark schemes.

## Controller/View Toggle

CFML MVC frameworks usually keep a `controllers` folder and a `views` folder in
the same parent, and match controller names and methods to view folders and
files. <kbd>CTRL</kbd>+<kbd>F1</kbd> (<kbd>CMD</kbd>+<kbd>F1</kbd> on a Mac)
jumps between a view and the controller method that corresponds to it. By
default, `controllers` and `handlers` are the controller folders and `views` is
the views folder. Set `controller_folders` and `view_folders` in your user
package settings to use other names.

## CommandBox

[CommandBox](https://www.ortussolutions.com/products/commandbox) is the default
build system for CFML files. Building a file (<kbd>F7</kbd>, or
<kbd>CTRL</kbd>+<kbd>B</kbd> on Windows and Linux and
<kbd>CMD</kbd>+<kbd>B</kbd> on a Mac) runs `box $file_name` in the file's folder
and shows the output in a panel. Choose the build from the menu with
<kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>B</kbd>
(<kbd>CMD</kbd>+<kbd>SHIFT</kbd>+<kbd>B</kbd> on a Mac). CommandBox has to be
installed, with the `box` binary on your `PATH` so it can be run in any
directory. See the
[CommandBox installation instructions](https://commandbox.ortusbooks.com/setup/installation).

## TestBox

[TestBox](https://www.ortussolutions.com/products/testbox) completions and
inline documentation are available for `BaseSpec` components. They are on by
default. Set `testbox_enabled` to `false` in your user package settings, or in a
project file, to turn them off for that scope. A project setting overrides the
package setting. Completions and documentation are offered in any CFC under a
folder named `tests` (other folder names can be set with `testbox_folders`), and
in any CFC that extends `testbox.system.BaseSpec`.

Three build variants run tests. `TestBox: Run Project Tests` runs the project's
tests and can be started from any CFML file. `TestBox: Run Directory Tests` runs
the tests in the active file's folder. `TestBox: Run Tests` runs the tests in
the active CFC. Open the build menu with
<kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>B</kbd>
(<kbd>CMD</kbd>+<kbd>SHIFT</kbd>+<kbd>B</kbd> on a Mac) to choose one. After
that, <kbd>CTRL</kbd>+<kbd>B</kbd> (<kbd>CMD</kbd>+<kbd>B</kbd> on a Mac) runs
the same variant again.

The directory and CFC variants need the active file to have been saved, and the
CFC variant only runs a `.cfc` file.

The runner and the other test settings are a `testbox` object, the same object
CommandBox reads from `box.json`. Each key is taken from the project file, then
from a `box.json` in a root folder of the project, then from your CFML package
settings. `runner` is a URL, or an array of URL objects (see
[the CommandBox `testbox` docs](https://commandbox.ortusbooks.com/package-management/box-json/testbox)).
There is no default runner, so set one of those. An array asks you which runner
to use. `reporter=json` is added to the URL, because that is the format this
package reads. The project variant calls the URL with no further change.

The directory variant adds `directory=dot.path.to.directory`, and the CFC
variant adds `testBundles=dot.path.to.directory.cfc`. Either replaces a
`directory` or `testBundles` already on the URL. The dotted path starts at
`testbox.tests_root`. A relative `tests_root` is resolved from the project file.
When `tests_root` is not set, the root is the folder of the project file, or, in
a window with no project file, the folder of the window that contains the file.

Results are shown in a panel. `testbox.reporter` chooses how much detail:
`text`, or `compacttext`, which is the default. <kbd>F4</kbd> and
<kbd>SHIFT</kbd>+<kbd>F4</kbd> step through the file stack of an error or a
failure, and Sublime Text opens each file at the reported line. Double-click a
file path to open it. When the server sees different paths than Sublime Text
does, for example because the server runs in a virtual machine, set
`testbox.results.server_root` and `testbox.results.sublime_root` to the two
roots so the stack traces open the right files.

Sublime Text waits `testbox.timeout` seconds for the runner, 300 by default. If
the runner does not respond in time, the results panel says so. Raise the
setting when the suite takes longer.

The default package settings list every TestBox setting.

## Framework One

[Framework One](https://github.com/framework-one/fw1) function completions and
`variables.framework` setting completions are off by default. Set `fw1_enabled`
to `true` in your user package settings, or in a project file, to turn them on.
A project setting overrides the package setting. The completions are offered in
`Application.cfc` and in Framework One controller, view, and layout files. The
folder names are `fw1_controller_folders`, `fw1_view_folders`, and
`fw1_layout_folders`. In controllers, Framework One methods are offered after
`framework.` and `fw.`.

## Acknowledgements

The following packages were used in the development of this package:

- <https://github.com/SublimeText/ColdFusion>
- <https://github.com/sublimehq/Packages>

The CFScript syntax is based on work done by Thomas Smith
([@Thom1729](https://github.com/Thom1729)) on the official JavaScript syntax:

- <https://github.com/sublimehq/Packages/pull/1009>

Special thanks to [@foundeo](https://github.com/foundeo) and
[cfdocs.org](https://cfdocs.org), from which this package gets its function and
tag data. Also, thanks to [@mjhagen](https://github.com/mjhagen), who helped get
this package off the ground.
