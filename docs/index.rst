*pyfomod* is a high-level fomod library written in python. No prior knowledge of xml
or fomod itself is required.

To start off, we'll import *pyfomod* as usual::

   >>> import pyfomod

.. _parsewrite:

Parsing and Writing
*******************

Fomod installers are packaged under a **fomod** subfolder and include a
**moduleconfig.xml** file and optionally a **info.xml** file.

.. py:function:: parse(source[, warnings], lineno=False)

    This function is used to parse either a package or loose files::

       >>> os.listdir("package")
       ['fomod', 'readme.txt', 'content']
       >>> os.listdir("package/fomod")
       ['info.xml', 'moduleconfig.xml']
       >>> root = pyfomod.parse("package")

       >>> payload = ("package/fomod/info.xml", "package/fomod/moduleconfig.xml")
       >>> root = pyfomod.parse(payload)

    As seen above, *source* can be either a
    `path-like object <https://docs.python.org/3/glossary.html#term-path-like-object>`_
    with the path to a package root or a tuple of (**path/to/info.xml**,
    **path/to/moduleconfig.xml**). If **info.xml** does not exist, ``None`` should be
    passed as its path.

    *warnings* is used to collect warnings related to parsing. See :ref:`validation`
    for more information on this.

    *lineno* is a boolean on whether to load the line numbers of the original package
    into each element of the tree. This is by default ``False`` due to the increased
    performance burden this option places on the parser.

    The returned *root* is the root of the fomod tree, see :py:class:`Root`.

    *pyfomod* can safely ignore most errors present in the physical files. Please note,
    however, that *pyfomod* does not support comments and they are not parsed at all.

.. py:function:: write(root, path)

    When you are finished reading and/or modifying your tree, write it::

       >>> pyfomod.write(root, "package")

    *root* should be the :py:class:`Root` of the fomod tree you're writing. *path*
    takes the same arguments types as *source* in :py:func:`parse`.

Root
****

.. py:class:: Root()

    Represents the root of the entire tree. An instance of this class is used to
    represent the entire tree in :py:func:`parse`/:py:func:`write` functions.

    Users looking to create a new tree should intantiate this class.

    All the following properties are read/write.

    .. py:attribute:: name

        A string with the package's name.

    .. py:attribute:: image

        A string with the path to the package's image.

    .. py:attribute:: author

        A string with the package's author.

    .. py:attribute:: version

        A string with the package's version.

    .. py:attribute:: description

        A string with the package's description.

    .. py:attribute:: website

        A string with the package's website.

    .. py:attribute:: conditions

        A :py:class:`Conditions` instance where it is checked whether the installer can
        start.

    .. py:attribute:: files

        A :py:class:`Files` instance that contains files/folders that will always be
        installed.

    .. py:attribute:: pages

        A :py:class:`Pages` instance that holds a list of installer pages.

    .. py:attribute:: file_patterns

        A :py:class:`FilePatterns` instance that contains a list of patterns that
        install files based on conditions.

Conditions
**********

.. py:class:: Conditions

    This class contains a list of codnitions. The fulfillment of these conditions leads
    to some action described in the containing class.

    There are four possible conditions:

    - flag condition - checks whether a flag has a specific value. See :py:class:`Flags`;
    - file condition - checks whether a file is missing or otherwise;
    - version condition - checks whether the game is at least the specified version;
    - nested conditions - a :py:class:`Conditions` objectm allowing for nested conditions.

    Instances of this class are dict-like objects, but hashable. Conditions held by the
    instance are defined by the key and value used.

    To add a version condition, the key must be `None` and the value a string with the
    version::

       >>> conditions[None] = "1.0.0"

    To add a flag condition, the key is a string with the flag name and value is a string
    with flag value::

       >>> conditions["flag_name"] = "flag_value"

    To add a file condition, the key is a string with the file path and the value is an
    enum `FileType` - this enum has `ACTIVE`, `INACTIVE` and `MISSING`::

       >>> conditions["file_path"] = FileType.MISSING

    Finally, to add a nested condition, the key is the object and the value is `None`::

       >>> nested = Conditions()
       >>> conditions[nested] = None

    .. py:attribute:: type

        This property accepts the enum `ConditionType`. This enum has either `AND` and
        `OR`. If `AND`, then all the conditions must be true to fulfill this instance,
        if `OR` only one condition needs to be true.

Files
*****

.. py:class:: Files

    The `Files` class is a container of files and folders to install. It produces
    dict-like objects that map file/folder sources to destination folder paths relative
    to the target folder (this target folder may vary per game/manager).

    To add a file is simple::

       >>> files["file_path"] = "dest"

    to add a folder, however, you must add a trailing slash to the key::

       >>> files["folder_path/"] = "dest"

Pages
*****

.. py:class:: Pages

    This class produces list-like objects that hold :py:class:`Page` instances.

    .. py:attribute:: order

        This controls the order in which the :py:class:`Page` objects appear.
        This property is an enum, `Order`, that has the values `ASCENDING`,
        `DESCENDING` and `EXPLICIT`.
        This orders the pages in this object according to their name. To note
        that only `EXPLICIT` preserves the order in this list.

Page
****

.. py:class:: Page

    This class produces list-like objects of :py:class:`Group` instances.

    These objects are the pages the user will eventually see when installing the mod.

    .. py:attribute:: name

        A string with the page's name/title.

    .. py:attribute:: order

        See :py:attr:`Pages.order`.

Group
*****

.. py:class:: Group

    Another list-like class, of :py:class:`Option` objects. Each of this class'
    instances represent a named section of a :py:class:`Page`.

    .. py:attribute:: name

        A string with the group's name/title.

    .. py:attribute:: type

        This property controls which options the user may select in this section.
        It is controlled via enum, `GroupType`, and each value is quite
        self-explanatory: `ALL`, `ANY`, `ATLEASTONE`, `ATMOSTONE`, `EXACTLYONE`.

    .. py:attribute:: order

        See :py:attr:`Pages.order`.

Option
******

.. py:class:: Option

    This class represents a single option the user can select.

    .. py:attribute:: name

        A string with the option's short text.

    .. py:attribute:: description

        A string with the option's long description.

    .. py:attribute:: image

        A string with a relative path to an image.

    .. py:attribute:: files

        A :py:class:`Files` object with the files/folders to install if this option
        is selected.

    .. py:attribute:: flags

        A :py:class:`Flags` object with the flags to set if this option is selected.

    .. py:attribute:: type

        This property controls the option type. It's usually an `OptionType` enum
        (and is recommended) which supports these values: `OPTIONAL`, `REQUIRED`,
        `RECOMMENDED`, `NOTUSABLE` or `COULDBEUSABLE`.

        This property could also be a :py:class:`Type` object, which allows for more
        complex type selection based on conditions.

Flags
*****

.. py:class:: Flags

    This class produces dict-like objects that map flag names to values::

        >>> flags = pyfomod.Flags()
        >>> flags['name'] = 'value'
        >>> dict(flags)
        {'name': 'value'}

Type
****

.. py:class:: Type

    This class produces dict-like objects that map :py:class:`Conditions` to
    `OptionType` (see :py:attr:`Option.type`) values. This class is used to find an
    appropriate type for an option - each pair's conditions are evaluated until one is
    met, which is the type used. If no conditions are evaluated to true,
    :py:attr:`default` is used as the option type.

    .. py:attribute:: default

        The default `OptionType` (see :py:attr:`Option.type`) used in case no other
        suitable types are found.

FilePatterns
************

.. py:class:: FilePatterns

    This class produces dict-like objects that map :py:class:`Conditions` to
    :py:class:`Files`. This class is used after :py:class:`Pages` when installing
    and installs the corresponding files for any conditions that were met.

.. _validation:

Validation
**********

*pyfomod* allows the user to validate the fomod tree - it checks for common
mistakes and incorrect values that, while valid, may lead to unexpected behaviour
during user installation.

You can check for warnings during parsing by passing a list to :py:func:`parse`::

    >>> warning_list = []
    >>> root = pyfomod.parse("package", warnings=warning_list)

You can also check for warnings during runtime by calling the :py:func:`validate` method
on any fomod object. Note that the possible errors produced in these two situations are
different, so if you want to find every possible warning be sure to use both.

.. py:function:: validate(**callbacks)

    This method validates the object and all its children, recursively. It returns a
    list of :py:class:`ValidationWarning` with the errors it found::

        >>> warnings_list = root.validate()

    The *callbacks* argument is a dict that maps strings to function objects. The keys
    of this dict should be *pyfomod* class names and the function objects should take a
    single argument - the instance the function is being run on - and return a list of
    :py:class:`ValidationWarning` objects.

    This argument is useful for adding more warnings to check for or even for running
    an arbitrary function recursively on the tree.

.. py:class:: ValidationWarning

    Each instance of this class refers to an error present in the fomod tree.

    .. py:attribute:: title

        A string with a suitable title.

    .. py:attribute:: msg

        A string describing the error.

    .. py:attribute:: elem

        The fomod object this error refers to.

    .. py:attribute:: critical

        A boolean on whether this error refers to something that may interfere with
        the installation process or is merely aesthetic.

Fomod Installer
***************

.. versionadded:: 1.0.0

You can start a non-gui installer from *pyfomod*. This will not actually install any
files or modify your filesystem in any way. It follows the same format and conventions
as the rest of *pyfomod* with one notable exception - the **priority** xml attribute
that is listed as ignored in :ref:`ignoredtags` is used in determining which files to
install.

You can continue to freely modify the fomod tree you passed to the installer with the
exception of removing objects. These changes will be reflected live. In order to
ensure maximum compatibility, you should use the objects the installer returns from its
:py:meth:`Installer.next` and :py:meth:`Installer.previous` methods instead of
:py:class:`Page`, :py:class:`Group` or :py:class:`Option` - these are read-only
equivalent to the corresponding classes in *pyfomod*.

To start, create an instance of :py:class:`Installer`.

.. py:class:: Installer(root[, path[, game_version[, file_type]]])

    Each instance of this class represents an ongoing installation. You can instance
    as many of these objects as you want, but keep in mind that modifications to a tree
    will be reflected on all installers that share them.

    *root* is a required argument that represents the root of the fomod tree. You can
    pass a :py:class:`Root` object which will be used directly by the installer. Any other
    than this will be passed along to :py:func:`parse` to produce a :py:class:`Root` object.

    If *path* is given, it will act as the root path for the fomod tree. Source lookups
    will be done using this path, although *pyfomod* will never modify any files. These
    lookups will allow :py:meth:`files` to provide the user with a complete dictionary
    of file sources and destinations, sorted acording to priority (meaning folders will
    be walked recursively for files and empty folders). Otherwise only logical path
    computations will be made.

    If *path* is not given but a string is passed as *root* then this will be assumed to
    be a root path for the fomod tree.

    *game_version* should be a string with the current version of the game you're running
    this installer for.

    *file_type* should be a function object that takes in a file name and returns a
    ``FileType`` concerning the file's presence in the target folder.

    During instancing of this class, if the conditions in :py:attr:`Root.conditions` are
    not met, a ``FailedCondition`` exception might be raised. To get the first visible
    page, run :py:meth:`next` with no arguments.

    .. py:method:: next([selected_options])

        Use this method to get the next page of the installer. Pass a list of selected
        options as *selected_options*.

        This will return an ``InstallerPage`` instance.

        This returns ``None`` when the installer is finished.

    .. py:method:: previous()

        Use this method to return to a previous page. Returns a tuple of
        ``(InstallerPage, [previously_selected_options])``.

        This returns ``None`` when the installer is at the start.

    .. py:method:: files()

        Returns a dictionary that maps file sources (strings) to file destinations
        (strings). If *path* is provided to the installer in a manner described above
        then actual files (or folders if they are empty) are used in the deictionary,
        otherwise only logical operations are made with the folders in the fomod tree.

        This should be called once the installer is finished but can be called at any
        time.

    .. py:method:: flags()

        Returns a dictionary that maps flag values (strings) to current flag values
        (strings). Although this does not impact the installation the user may debug
        installers by calling this during the installation.

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
  :py:func:`parse` function was passed the keyword argument `lineno=True`. Otherwise,
  `self.lineno` is `None`

The **info.xml** file's root is stored apart from **moduleconfig.xml**'s root, at
`root._info`, where `root` is the object returned by :py:func:`parse`. Since there is
no consensus on what the **info.xml** file should contain or even the format/schema,
*pyfomod* assumes the user knows what it's loading and will respect the tag's case.
The `root._info` object belongs to the `Info` class. This class has two methods that
handle extracting and modifying information on this file: `get_text` and  `set_text`.
These assume the information is stored in the text of children of the `<fomod>` root
element and search for a case-insensitive tag. The user is free to extract or modify
information using the `_attrib` and `_children` attributes in the object.

.. _ignoredtags:

Ignored Tags and Attributes
---------------------------

Some of the tags and attributes present in the fomod schema are ignored by the API
both because they're either not very useful or have fallen out of use or in order
to streamline user experience.

These are not removed or lost however, they're both accessible as described above.

The following tags are ignored:

- `fommDependency`

The following attributes are ignored:

- `position`, `colour` - [**moduleName**]
- `showImage`, `showFade`, `height` - [**moduleImage**]
- `alwaysInstall`, `installIfUsable`, `priority` - [**file**, **folder**]
