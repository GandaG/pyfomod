*pyfomod* is a high-level fomod library written in python. No prior knowledge of xml
or fomod itself is required.

To start off, we'll import *pyfomod* as usual::

   >>> import pyfomod

.. _parsewrite:

Parsing and Writing
*******************

Fomod installers are packaged under a **fomod** subfolder and include a
**moduleconfig.xml** file and optionally a **info.xml** file. If you wish to read
a physical installer simply pass the package path to the *parse* function::

   >>> os.listdir("package")
   ['fomod', 'readme.txt', 'content']
   >>> os.listdir("package/fomod")
   ['info.xml', 'moduleconfig.xml']

   >>> root = pyfomod.parse("package")

This *root* is the entire root of the fomod installer, see :ref:`root`. There may
be errors with the physical files but  *pyfomod* can safely ignore them.

If the installer is not packaged in a conventional manner, you may also pass a tuple or
list with the file paths. The paths must be strings and be in the order: **info.xml**,
**moduleconfig.xml**::

   >>> payload = ("package/fomod/info.xml", "package/fomod/moduleconfig.xml")
   >>> root = pyfomod.parse(payload)

When you are finished reading and/or modifying your installer, write it::

   >>> pyfomod.write(root, "package")

The second argument to `write` is the same as for `parse`, either the package or a
tuple/list with the file paths.

.. _root:

Root
****

The `Root` class is the literal root of your installer - it serves as the entry point
for every operation.

In here the following simple read/write properties are defined:

- `name` - (string) the package's name;
- `image` - (string) the path to the package's image;
- `author` - (string) the package's author;
- `version` - (string) the package's version;
- `description` - (string) the package's description;
- `website` - (string) the package's website;

The property `conditions` holds a :ref:`conditions` instance where it is
checked whether the installer can start.

The property `files` holds a :ref:`files` instance that contains files/folders that
will always be installed.

The property `pages` holds a :ref:`pages` instance that holds a list of installer pages. More info on that section.

Finally, the property `file_patterns` holds a :ref:`filepatterns` instance that contains
a list of patterns that install files based on conditions. More info on that section.

.. _conditions:

Conditions
**********

The `Conditions` class contains a list of conditions. The fulfillment of these
conditions leads to some action described in the appropriate section.

To start, the property `type` accepts the enum `ConditionType`. This enum has either
`AND` and `OR`. If `AND`, then all the conditions must be true to fulfill this instance,
if `OR` only one condition needs to be true.

There are four possible items to be added here:

- flag condition - checks whether a flag has a specific value. See :ref:`flags`;
- file condition - checks whether a file is missing or otherwise;
- version condition - checks whether the game is at least the specified version.

The last possible item is another `Conditions`, allowing conditions to be nested.

This class functions like a dictionary (has the same methods as the stdlib dict) but
adding (setting) has a few rules.

To add a version condition, the key must be `None` and the value a string with the
version::

   >>> conditions[None] = "1.0.0"

To add a flag condition, the key is a string with the flag name and value is a string
with flag value::

   >>> conditions["flag_name"] = "flag_value"

To add a file condition, the key is a string with the file path and the value is an
enum `FileType` - this enum has `ACTIVE`, `INACTIVE` and `MISSING`::

   >>> conditions["file_path"] = FileType.MISSING

Finally, to add a nested `Conditions`, the key is the object and the value is `None`::

   >>> nested = Conditions()
   >>> conditions[nested] = None

.. _files:

Files
*****

The `Files` class is a container of files and folders to install. It behaves like a
stdlib dict that maps file/folder sources to destination folder paths relative to the
target folder (this target folder may vary per game/manager).

To add a file is simple::

   >>> files["file_path"] = "dest"

to add a folder, however, you must add a trailing slash to the key::

   >>> files["folder_path/"] = "dest"

.. _pages:

Pages
*****

The `Pages` class is a list of :ref:`page` objects that behaves exactly like a stdlib
list.

There is a single property, `order` that controls the order in which the `Page`'s
appear. This property is an enum, `Order`, that has the values `ASCENDING`,
`DESCENDING` and `EXPLICIT`. This orders the pages in this object according to their
name. To note that only `EXPLICIT` preserves the order in this list.

.. _page:

Page
****

The `Page` class is a list of :ref:`group` objects that behaves exactly like a stdlib
list. This class is a page the user will eventually see when installing the mod.

Has the property `name` that holds a string that serves as the page name, the property
`order` that is identical to the explained in :ref:`pages` and the property `conditions`
that controls whether this page will be visible to the user.

.. _group:

Group
*****

The `Group` class is a list of :ref:`option` objects that behaves exactly like a stdlib
list. This class is a named section of a :ref:`page`.

Has the property `name` that holds a string that serves as the page name, the property
`order` that is identical to the explained in :ref:`pages` and the property `type`,
an enum `GroupType` that controls which options the user may select in this section,
each value is quite self-explanatory: `ALL`, `ANY`, `ATLEASTONE`, `ATMOSTONE`,
`EXACTLYONE`.

.. _option:

Option
******

The `Option` class represents a single option the user can select.

This class has the following properties:

- `name` (string) - the option's short text;
- `description` (string) - the option's long description;
- `image` (string) - a path to an image relative to the package root;
- `files` (:ref:`files`) - the files/folders to install if this option is selected;
- `flags` (:ref:`flags`) - the flags to set if this option is selected;
- `type` (enum `OptionType` or :ref:`type`) - the option type, it is recommended to use
  the enum but :ref:`type` may be used for complex cases.

The enum `OptionType` has the possible values:
  - `OPTIONAL` - this option may be selected and unselected;
  - `REQUIRED` - this option is always selected and can't be unselected;
  - `RECOMMENDED` - this option comes pre-selected but may be unselected;
  - `NOTUSABLE` - this option can't be selected;
  - `COULDBEUSABLE` - this option can be selected but produces a warning.

.. _flags:

Flags
*****

The `Flags` class holds the flags that are to be set when an :ref:`option` is selected.
This class behaves exactly like a stdlib dict that maps flag names as string to flag
values as strings.

.. _type:

Type
****

The `Type` class holds a mapping of :ref:`conditions` to `OptionType` and behaves
exactly like a stdlib dict.

This class finds a type for the corresponding :ref:`option` by finding a fulfilled
:ref:`conditions` key and using the `OptionType` value.

It has a `default` property that is the enum `OptionType` and is used as the option type
when no :ref:`conditions` is fulfilled.

.. _filepatterns:

File Patterns
*************

The `FilePatterns` class holds a mapping of :ref:`conditions` to :ref:`files` and
behaves exactly like a stdlib dict.

This class is used after :ref:`pages` when installing and for any :ref:`conditions`
keys that are fulfilled installs the corresponding :ref:`files` values.

.. _validation:

Validation
**********

*pyfomod* allows the user to validate the fomod installer - it checks for common
mistakes and incorrect values that, while valid, may lead to unexpected behaviour
during user installation.

You can check for warnings during parsing by passing a list to `parse`::

    >>> warning_list = []
    >>> root = pyfomod.parse("package", warnings=warning_list)

You can also check for warnings during runtime by calling the `validate()` method
on any fomod object - this will validate the object itself and any children::

    >>> warning_list = root.validate()

Note that the possible errors produced in these two situations are different, so if
you want to find every possible warning be sure to use both.

The warnings are instances of `ValidateWarning`, which has the following attributes:

- `title` - (string) A suitable warning title;
- `msg` - (string) A message explaining the warning;
- `elem` - (object) The fomod object this warning refers to;
- `critical` - (boolean) Whether this warning refers to something that may interfere with
  the installation process.

Low-Level Access
****************

Although *pyfomod* is a high-level library all data is preserved and is accessible
through a private interface. This access is not recommended, may break pyfomod's
normal use if mishandled and may change at any point with no deprecation or grace
period.

All classes, regardless of whether they're mentioned above or referred here as "hidden",
can be validated individually or written to a string via the `to_string` method.

All classes used in *pyfomod* that have a corresponding xml element hold data in similar
ways:

- All initial attributes when parsing are stored in `self._attrib` - these may be
  overwritten when serializing the object;
- All unused children are stored in `self._children` - this is a dictionary of
  "tag" -> ({attribute dictionary}, "text")
- The line number of the original element is stored in `self.lineno` if the initial
  `parse` function was passed the keyword argument `lineno=True`. Otherwise,
  `self.lineno` is `None`

The **info.xml** file's root is stored apart from **moduleconfig.xml**'s root, at
`root._info`, where `root` is the object returned by `parse`. Since there is no
consensus on what the **info.xml** file should contain or even the format/schema,
*pyfomod* assumes the user knows what it's loading and will respect the tag's case.
The `root._info` object belongs to the `Info` class. This class has two methods that
handle extracting and modifying information on this file: `get_text` and  `set_text`.
These assume the information is stored in the text of children of the `<fomod>` root
element and search for a case-insensitive tag. The user is free to extract or modify
information using the `_attrib` and `_children` attributes in the object.
