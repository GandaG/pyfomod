##########
Validation
##########

Once again, this has been run for the entire doc::

    >>> import pyfomod


**************************
Validating files and trees
**************************

Validating installers is simple::

    >>> pyfomod.validate('path/to/info.xml')  # you can pass a filename directly
    True

    >>> pyfomod.validate('path/to/ModuleConfig.xml')
    True

    >>> root = pyfomod.new()
    >>> pyfomod.validate(root)  # or a pyfomod tree
    True

    >>> with open('path/to/info.xml', 'r') as info_file:  # and even other types!
    ...     pyfomod.validate(info_file)
    True

The :func:`~pyfomod.validate` function only provides a boolean on
whether the installer is valid or not. This can be great for a quick check but
provides very little useful information.

When you need to know exactly what's wrong with your installer, you should use
:func:`~pyfomod.assert_valid`::

    >>> pyfomod.assert_valid('path/to/info.xml')  # everything ok here
    >>> pyfomod.assert_valid('path/to/ModuleConfig.xml')  # missing an element!
    Traceback (most recent call last):
     ...
    AssertionError: Element 'config': Missing child element(s). Expected is ( moduleName ).


****************************
Checking for common mistakes
****************************

There are many common mistakes or errors that can occur in a fomod installer
that are considered valid by the schema::

    >>> with open('path/to/info.xml', 'r') as info_file:
    ...     print(info_file.read())  # our info.xml file is pretty empty right now
    <fomod/>

    >>> pyfomod.check_for_errors('path/to/info.xml')
    [FomodError(line=1,
                title='Offline Installer',
                msg='The installer has no website specified.',
                tag='fomod'),
     FomodError(line=1,
                title='Versionless Installer',
                msg='The installer has no version specified.',
                tag='fomod'),
     FomodError(line=1,
                title='Installer With No Name',
                msg='The installer has no name specified.',
                tag='fomod'),
     FomodError(line=1,
                title='Unsigned Installer',
                msg='The installer has no author specified.',
                tag='fomod')]

As you can see, the errors are reported cleanly so you can organize them in any
way you want. Let's fix those errors::

    >>> with open('path/to/info.xml', 'r') as info_file:
    ...     print(info_file.read())
    <fomod>
        <Name>Example Name</Name>
        <Author>Example Author</Author>
        <Version>0</Version>
        <Website>www.example.com</Website>
    </fomod>

    >>> pyfomod.check_for_errors('path/to/info.xml')
    []


Adding new errors
=================

If the existing errors are not enough for you, adding more is an option::

    class IDError(pyfomod.ErrorChecker):
        """
        As an example, consider an error any ID tag below <fomod>
        in the info.xml file.
        """
        @staticmethod
        def tag():
            return ('fomod',)

        def title(self):
            return "No ID Please"

        def error_string(self):
            return "I don't need no ID."

        def check(self, root, element, path):
            super().check(root, element, path)

            for child in element:
                if child.tag == 'ID':
                    return True
            return False

By simply subclassing :class:`~pyfomod.ErrorChecker` you'll be
adding another error to check for. To understand more about which methods to
use you should really check out the API reference.


Replacing existing errors
=========================

Sometimes an error just isn't working out for you and you need to modify it.
Much like adding new ones, it involves subclassing either
:class:`~pyfomod.ErrorChecker` or the error itself and naming
your sublcass the same as the error you're replacing::

    class UnusedFilesError(pyfomod.UnusedFilesError):
        """
        As an example, we'll be ignoring readme.txt if unused
        by the installer.
        """
        def check(self, root, element, path):
            super().check(root, element, path)

            try:
                self.unused_files.remove('readme.txt')
            except ValueError:
                pass  # if the file is not in the unused list, ignore

            if len(self.unused_files) == 0:
                return False
            return True

To complete "remove" an existing error simple override
:meth:`~pyfomod.ErrorChecker.check`::

    class UnusedFilesError(pyfomod.UnusedFilesError):
        def check(self, root, element, path):
            return False

And now you'll never see the :class:`~pyfomod.UnusedFilesError` again.
