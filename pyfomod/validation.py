# Copyright 2016 Daniel Nunes
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module holds all functions needed to validate and check the
installer for errors.
"""

import collections
import os
from abc import ABCMeta, abstractmethod

from lxml import etree

from .io import get_installer_files

FOMOD_SCHEMA_TREE = etree.parse(
    os.path.join(os.path.dirname(__file__), 'fomod.xsd')).getroot()
FOMOD_SCHEMA = etree.XMLSchema(FOMOD_SCHEMA_TREE)


def assert_valid(tree, schema=None):
    """
    Validates a FOMOD tree. Raises an :class:`AssertionError` if invalid
    with the validation error as the exception message.

    Args:
        tree: The tree to validate.
            ``tree`` can be any of the following:

                - a :class:`~pyfomod.parser.FomodElement`
                - a file name/path
                - a file object
                - a file-like object
                - a URL using the HTTP or FTP protocol

        schema (optional): A specific schema to validate against.
            If ``None`` then default schema is used.
            ``schema`` can be any of the following:

                - an lxml Element or any subclass of it
                - an lxml XMLSchema
                - an lxml ElementTree

    Raises:
        AssertionError: If ``tree`` fails to validate. The exception message
            contains the validation error.
    """
    if schema is None:
        schema = FOMOD_SCHEMA
    try:
        schema = etree.XMLSchema(schema)
    except TypeError:
        pass
    if not isinstance(tree, (etree._Element, etree._ElementTree)):
        tree = etree.parse(tree)
    schema.assert_(tree)


def validate(tree, schema=None):
    """
    Validates a FOMOD tree.

    Args:
        tree: The tree to validate.
            ``tree`` can be any of the following:

                - a :class:`~pyfomod.parser.FomodElement`
                - a file name/path
                - a file object
                - a file-like object
                - a URL using the HTTP or FTP protocol

        schema (optional): A specific schema to validate against.
            If ``None`` then default schema is used.
            ``schema`` can be any of the following:

                - an lxml Element or any subclass of it
                - an lxml XMLSchema
                - an lxml ElementTree

    Returns:
        bool: True if ``tree`` is valid, False otherwise.
    """
    if schema is None:
        schema = FOMOD_SCHEMA
    try:
        schema = etree.XMLSchema(schema)
    except TypeError:
        pass
    if not isinstance(tree, (etree._Element, etree._ElementTree)):
        tree = etree.parse(tree)
    return schema.validate(tree)


ERROR_DICT = {}


FomodError = collections.namedtuple('FomodError', 'lines title msg')
"""
This ``namedtuple`` represents an error.

Attributes:
    lines (int): The lines at which the error occured.
    title (str): The error's title.
    msg (str): A message explaining the error.
"""


class _MetaErrorChecker(ABCMeta):
    """
    Metaclass used to auto-register error checker subclasses.
    User-defined subclasses outside of this module are defined after and so
    can replace these subclasses.
    """
    def __init__(cls, clsname, bases, attrs):
        super(_MetaErrorChecker, cls).__init__(clsname, bases, attrs)
        if clsname != 'ErrorChecker':
            ERROR_DICT[clsname] = cls


class ErrorChecker(object, metaclass=_MetaErrorChecker):
    """
    Base class for error checking.
    Used by *check_for_errors* function.
    Subclasses should fill in all relevant fields.
    """

    def __init__(self):
        super(ErrorChecker, self).__init__()

        # this is defined in the base class since most subclasses will use it.
        self.error_tag = None

    @property
    def needs_path(self):
        """
        Subclasses should only change this if they need to
        be passed a path to the installer in the *check* method.

        Returns:
            bool: Whether this class needs access to a physical path.
        """
        return False

    @staticmethod
    @abstractmethod
    def tag():
        """
        Should return a tuple/list of strings with
        the tags that should be checked with the *check* method.

        Returns:
            tuple(str):
                A tuple of tags that should be checked
                with :func:`~ErrorChecker.check`.
        """
        raise NotImplementedError()

    @abstractmethod
    def title(self):
        """
        Should return the title of the error.

        Returns:
            str: The error title.
        """
        raise NotImplementedError()

    @abstractmethod
    def error_string(self):
        """
        Should return the error string.

        Returns:
            str: A message explaining the error.
        """
        raise NotImplementedError()

    @abstractmethod
    def check(self, root, element, installer_path):
        """
        The method that runs on the tags specified to check
        for a specific error. Subclasses should call :func:`super`

        Args:
            root (~pyfomod.parser.FomodElement):
                The root of the tree being evaluated.
            element (~pyfomod.parser.FomodElement):
                The current element being evaluated.
            installer_path (str): The path to the physical
                package

        Returns:
            bool:
                Should return True if the error occurs,
                False otherwise.
        """
        self.error_tag = element.tag
        return False


class NoNameError(ErrorChecker):
    """
    Checks for installers with no Name specified.
    """

    @staticmethod
    def tag():
        return ('fomod',)

    def title(self):
        return "Installer With No Name"

    def error_string(self):
        return "The installer has no name specified."

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)
        for child in element:
            if child.tag == 'Name':
                return False
        return True


class NoAuthorError(ErrorChecker):
    """
    Checks for installers with no Author specified.
    """

    @staticmethod
    def tag():
        return ('fomod',)

    def title(self):
        return "Unsigned Installer"

    def error_string(self):
        return "The installer has no author specified."

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)
        for child in element:
            if child.tag == 'Author':
                return False
        return True


class NoVersionError(ErrorChecker):
    """
    Checks for installers with no Version specified.
    """

    @staticmethod
    def tag():
        return ('fomod',)

    def title(self):
        return "Versionless Installer"

    def error_string(self):
        return "The installer has no version specified."

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)
        for child in element:
            if child.tag == 'Version':
                return False
        return True


class NoWebsiteError(ErrorChecker):
    """
    Checks for installers with no Website specified.
    """

    @staticmethod
    def tag():
        return ('fomod',)

    def title(self):
        return "Offline Installer"

    def error_string(self):
        return "The installer has no website specified."

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)
        for child in element:
            if child.tag == 'Website':
                return False
        return True


class EmptyInstError(ErrorChecker):
    """
    Checks for empty installers.
    """

    @staticmethod
    def tag():
        return ('config',)

    def title(self):
        return "Empty Installer"

    def error_string(self):
        return "The installer is empty."

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)
        for child in element:
            if (child.tag == 'moduleDependencies' or
                    child.tag == 'requiredInstallFiles' or
                    child.tag == 'installSteps' or
                    child.tag == 'conditionalFileInstalls'):
                return False
        return True


class EmptySourceError(ErrorChecker):
    """
    Checks if source fields in folder/file tags are empty.
    """

    @staticmethod
    def tag():
        return ('file', 'folder')

    def title(self):
        return "Empty Source Fields"

    def error_string(self):
        return "The source folder(s) under " \
               "the tag {} were empty.".format(self.error_tag)

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)
        return not element.get('source')


class UnusedFilesError(ErrorChecker):
    """
    Checks if there are any unused files in the package.
    """

    def __init__(self):
        super(UnusedFilesError, self).__init__()
        self.unused_files = []

    @property
    def needs_path(self):
        return True

    @staticmethod
    def tag():
        return ('config',)

    def title(self):
        return "Unused Files"

    def error_string(self):
        error = "The following file(s) are included within the package" \
                " but are not used:"
        for path in self.unused_files:
            error += "\n    {}".format(path)
        return error

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)

        used_files = []
        used_folders = []

        for elem in element.iterfind('.//file'):
            path = os.path.join(installer_path, elem.get('source'))
            used_files.append(path.replace('/', os.sep))
        for elem in element.iterfind('.//folder'):
            path = os.path.join(installer_path, elem.get('source'))
            used_folders.append(path.replace('/', os.sep))
        for elem in element.iterfind('.//image'):
            path = os.path.join(installer_path, elem.get('path'))
            used_files.append(path.replace('/', os.sep))
        for elem in element.iterfind('.//moduleImage'):
            path = os.path.join(installer_path, elem.get('path'))
            used_files.append(path.replace('/', os.sep))

        try:
            used_files.extend(get_installer_files(installer_path))
        except IOError:
            # in case no fomod folder exists
            pass

        for path, dnames, fnames in os.walk(installer_path):
            for name in dnames:
                if os.path.join(path, name) in used_folders:
                    del dnames[dnames.index(name)]
            for name in fnames:
                if os.path.join(path, name) not in used_files:
                    fpath = os.path.relpath(os.path.join(path, name),
                                            installer_path)
                    self.unused_files.append(fpath)

        return self.unused_files


class MissingFolderError(ErrorChecker):
    """
    Checks for folders in a *source* field in a *folder* tag that are missing.
    """

    @staticmethod
    def tag():
        return ('folder',)

    def title(self):
        return "Missing Source Folders"

    def error_string(self):
        return "The source folder(s) under the tag {} weren't found " \
               "inside the package.".format(self.error_tag)

    @property
    def needs_path(self):
        return True

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)
        return not os.path.isdir(os.path.join(installer_path,
                                              element.get('source')))


class MissingFileError(ErrorChecker):
    """
    Checks for files in a *source* field in a *file* tag that are missing.
    """

    @staticmethod
    def tag():
        return ('file',)

    def title(self):
        return "Missing Source Files"

    def error_string(self):
        return "The source file(s) under the tag {} weren't found " \
               "inside the package.".format(self.error_tag)

    @property
    def needs_path(self):
        return True

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)
        return not os.path.isfile(os.path.join(installer_path,
                                               element.get('source')))


class MissingImageError(ErrorChecker):
    """
    Checks for missing images in image tag sources.
    """

    @staticmethod
    def tag():
        return ('moduleImage', 'image')

    def title(self):
        return "Missing Images"

    def error_string(self):
        return "The image(s) under the tag {} weren't " \
               "found inside the package.".format(self.error_tag)

    @property
    def needs_path(self):
        return True

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)
        return not os.path.isfile(os.path.join(installer_path,
                                               element.get('path')))


class FlagLabelMismatchError(ErrorChecker):
    """
    Checks that dependent flag labels are actually created.
    """

    @staticmethod
    def tag():
        return ('flagDependency',)

    def title(self):
        return "Mismatched Flag Labels"

    def error_string(self):
        return "The flag label that {} is dependent on is never " \
               "created during installation.".format(self.error_tag)

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)
        for elem in root.iterfind('.//flag'):
            if elem.get('name') == element.get('flag'):
                return False

        return True


class FlagValueMismatchError(ErrorChecker):
    """
    Checks that dependent flag values are actually set.
    """

    @staticmethod
    def tag():
        return ('flagDependency',)

    def title(self):
        return "Mismatched Flag Values"

    def error_string(self):
        return "The flag value that {} is " \
               "dependent on is never set.".format(self.error_tag)

    def check(self, root, element, installer_path):
        super().check(root, element, installer_path)

        # check if the flag label actually exists
        # no point in showing this error if the label doesn't even exist
        label_found = False

        for elem in root.iterfind('.//flag'):
            if elem.get('name') == element.get('flag'):
                label_found = True
                if elem.text == element.get('value'):
                    return False

        return label_found


def check_for_errors(tree, path=''):
    """
    Checks for common mistakes in FOMOD installers.

    Args:
        tree: The tree to validate.
            ``tree`` can be any of the following:

                - a :class:`~pyfomod.parser.FomodElement`
                - a file name/path
                - a file object
                - a file-like object
                - a URL using the HTTP or FTP protocol

        path (str): The path to the package to install.
            Used for checking errors that involve physical files.

    Returns:
        list(FomodError):
            A list of :class:`FomodError` tuples,
            that represent each error/mistake caught in ``tree``.

    Raises:
        AssertionError: In case the FOMOD in ``tree`` is not valid.
            See :func:`assert_valid`.

    Note:
        You can pass any path to this function, even one without a
        physical FOMOD installer present. This allows you to check
        for errors before commiting to a physical installer.
    """
    assert_valid(tree)

    if isinstance(tree, etree._ElementTree):
        tree = tree.getroot()
    elif not isinstance(tree, etree._Element):
        if not path:
            path = tree
        tree = etree.parse(tree)

    # build the tag -> errors dictionary
    # easier to select errors to check
    error_tag_dict = {}
    for error in ERROR_DICT.values():
        for tag in error.tag():
            if tag in error_tag_dict:
                error_tag_dict[tag].append(error())
            else:
                error_tag_dict[tag] = [error()]

    # start iterating and checking
    error_line_dict = {}
    for element in tree.iter():
        if element.tag in error_tag_dict:
            for error in error_tag_dict[element.tag]:
                if error.needs_path and not os.path.isdir(path):
                    continue

                if error.check(tree, element, path):
                    error_line_dict.setdefault(error,
                                               []).append(element.sourceline)

    return [FomodError(error_line_dict[error],
                       error.title(),
                       error.error_string()) for error in error_line_dict]
