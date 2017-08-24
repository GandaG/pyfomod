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

import os

from lxml import etree

from .io import get_installer_files
from .parser import Root

INFO_SCHEMA_TREE = etree.parse(
    os.path.join(os.path.dirname(__file__), 'info.xsd')).getroot()
INFO_SCHEMA = etree.XMLSchema(INFO_SCHEMA_TREE)
CONF_SCHEMA_TREE = etree.parse(
    os.path.join(os.path.dirname(__file__), 'conf.xsd')).getroot()
CONF_SCHEMA = etree.XMLSchema(CONF_SCHEMA_TREE)


def validate_installer(installer):
    """
    Checks if the `installer` is valid.

    Args:
        installer:
            Accepts as arguments a parsed Root object, a tuple or list of
            two parsed lxml trees (info and config, in that order) or a valid
            path to an installer. The path follows the same rules as when given
            to get_installer_files.

    Returns:
        bool: True if the installer is valid, False if not.

    Raises:
        ValueError: If the argument passed does not comply with the
            rules above.
    """
    # the variable to hold the info and config trees
    installer_trees = None

    # check if it's a parsed Root object - dead end for now
    if isinstance(installer, Root):
        raise NotImplementedError

    # checks if it's a tuple of parsed lxml trees
    if isinstance(installer, (list, tuple)):
        try:
            installer_trees = (etree.ElementTree(installer[0].getroot()),
                               etree.ElementTree(installer[1].getroot()))
        except AttributeError:
            installer_trees = (etree.ElementTree(installer[0]),
                               etree.ElementTree(installer[1]))

    if installer_trees is None:
        # last, check if it's a path to the installer
        try:
            file_paths = get_installer_files(installer)
            installer_trees = (etree.parse(file_paths[0]),
                               etree.parse(file_paths[1]))
        except IOError:
            # if installer_trees is still None the argument is invalid
            raise ValueError

    # return the validity of the documents
    return (INFO_SCHEMA.validate(installer_trees[0]) and
            CONF_SCHEMA.validate(installer_trees[1]))


ERROR_LIST = []


class ErrorChecker(object):
    """
    Base class for error checking.
    Used by *check_for_errors* function.
    Subclasses should fill in all relevant fields.
    """

    @staticmethod
    def tag():
        """
        Should return a tuple/list of strings with
        the tags that should be checked with the *run* method.
        """
        pass

    @staticmethod
    def title():
        """
        Should return the title of the error.
        """
        pass

    @staticmethod
    def error_string():
        """
        Should return the error string. A pair of braces {}
        can be used if multiple tags need to be mentioned.
        """
        pass

    @staticmethod
    def needs_path():
        """
        Subclasses should only change this if they need to
        be passed a path to the installer in the *check* method.
        """
        return False

    @staticmethod
    def check(root, element, installer_path):
        """
        The method that runs on the tags specified to check
        for a specific error.
        """
        pass


class EmptyInstError(ErrorChecker):
    """
    Checks for empty installers.
    """

    @staticmethod
    def tag():
        return ('config',)

    @staticmethod
    def title():
        return "Empty Installer"

    @staticmethod
    def error_string():
        return "The installer is empty."

    @staticmethod
    def check(root, element, installer_path):
        del root, installer_path
        for child in element:
            if (child.tag == 'moduleDependencies' or
                    child.tag == 'requiredInstallFiles' or
                    child.tag == 'installSteps' or
                    child.tag == 'conditionalFileInstalls'):
                return False
        return True


ERROR_LIST.append(EmptyInstError)


class EmptySourceError(ErrorChecker):
    """
    Checks if source fields in folder/file tags are empty.
    """

    @staticmethod
    def tag():
        return ('file', 'folder')

    @staticmethod
    def title():
        return "Empty Source Fields"

    @staticmethod
    def error_string():
        return "The source folder(s) under the tag {} were empty."

    @staticmethod
    def check(root, element, installer_path):
        del root, installer_path
        return not element.get('source')


ERROR_LIST.append(EmptySourceError)


class MissingFolderError(ErrorChecker):
    """
    Checks for folders in a *source* field in a *folder* tag that are missing.
    """

    @staticmethod
    def tag():
        return ('folder',)

    @staticmethod
    def title():
        return "Missing Source Folders"

    @staticmethod
    def error_string():
        return "The source folder(s) under the tag {} weren't found " \
               "inside the package."

    @staticmethod
    def needs_path():
        return True

    @staticmethod
    def check(root, element, installer_path):
        del root
        if not element.get('source'):
            return False
        return not os.path.isdir(os.path.join(installer_path,
                                              element.get('source')))


ERROR_LIST.append(MissingFolderError)


class MissingFileError(ErrorChecker):
    """
    Checks for files in a *source* field in a *file* tag that are missing.
    """

    @staticmethod
    def tag():
        return ('file',)

    @staticmethod
    def title():
        return "Missing Source Files"

    @staticmethod
    def error_string():
        return "The source file(s) under the tag {} weren't found " \
               "inside the package."

    @staticmethod
    def needs_path():
        return True

    @staticmethod
    def check(root, element, installer_path):
        del root
        if not element.get('source'):
            return False
        return not os.path.isfile(os.path.join(installer_path,
                                               element.get('source')))


ERROR_LIST.append(MissingFileError)


class MissingImageError(ErrorChecker):
    """
    Checks for missing images in image tag sources.
    """

    @staticmethod
    def tag():
        return ('moduleImage', 'image')

    @staticmethod
    def title():
        return "Missing Images"

    @staticmethod
    def error_string():
        return "The image(s) under the tag {} weren't " \
               "found inside the package."

    @staticmethod
    def needs_path():
        return True

    @staticmethod
    def check(root, element, installer_path):
        del root
        return not os.path.isfile(os.path.join(installer_path,
                                               element.get('path')))


ERROR_LIST.append(MissingImageError)


class FlagLabelMismatchError(ErrorChecker):
    """
    Checks that dependent flag labels are actually created.
    """

    @staticmethod
    def tag():
        return ('flagDependency',)

    @staticmethod
    def title():
        return "Mismatched Flag Labels"

    @staticmethod
    def error_string():
        return "The flag label that {} is dependent on is never " \
               "created during installation."

    @staticmethod
    def check(root, element, installer_path):
        del installer_path
        if not element.get('value'):
            return False

        for elem in root.findall('.//flag'):
            if elem.get('name') == element.get('flag'):
                return False

        return True


ERROR_LIST.append(FlagLabelMismatchError)


class FlagValueMismatchError(ErrorChecker):
    """
    Checks that dependent flag values are actually set.
    """

    @staticmethod
    def tag():
        return ('flagDependency',)

    @staticmethod
    def title():
        return "Mismatched Flag Values"

    @staticmethod
    def error_string():
        return "The flag value that {} is dependent on is never set."

    @staticmethod
    def check(root, element, installer_path):
        del installer_path
        if not element.get('value'):
            return False

        for elem in root.findall('.//flag'):
            if (elem.get('name') == element.get('flag') and
                    elem.text == element.get('value')):
                return False

        return True


ERROR_LIST.append(FlagValueMismatchError)


def check_for_errors(installer):
    """
    Call this function to check for errors.
    Refer to ErrorChecker subclasses for more information.

    Args:
        installer:
            Accepts a Root object, a tuple/list of
            parsed lxml trees as (info, config) and
            a path to the package. Error checks that
            require a package path will only be checked
            if a package path is given as the argument.

    Returns:
        list(tuple):
            a list of tuples as: (lines, title, message, tag)
    """

    # the list to hold the final tuples
    checked_errors = []

    # the variable to hold the lxml trees
    installer_trees = None

    # boolean that checks if the argument is a valid path
    installer_is_path = False

    # build the tag -> errors dictionary
    # easier to select errors to check
    error_tag_dict = {}
    for error in ERROR_LIST:
        for tag in error.tag():
            if tag in error_tag_dict:
                error_tag_dict[tag].append(error)
            else:
                error_tag_dict[tag] = [error]

    # check if it's a parsed Root object - dead end for now
    if isinstance(installer, Root):
        raise NotImplementedError

    # checks if it's a tuple of parsed lxml trees
    if isinstance(installer, (list, tuple)):
        try:
            installer_trees = (etree.ElementTree(installer[0].getroot()),
                               etree.ElementTree(installer[1].getroot()))
        except AttributeError:
            installer_trees = (etree.ElementTree(installer[0]),
                               etree.ElementTree(installer[1]))

    if installer_trees is None:
        # last, check if it's a path to the installer
        try:
            file_paths = get_installer_files(installer)
            installer_trees = (etree.parse(file_paths[0]),
                               etree.parse(file_paths[1]))
            installer_is_path = True
            if (os.path.dirname(file_paths[0]) == installer and
                    os.path.dirname(file_paths[1]) == installer):
                installer = os.path.join(installer, '..')
        except IOError:
            # if installer_trees is still None the argument is invalid
            raise ValueError

    # start iterating and checking
    for element in installer_trees[1].getroot().iter():
        if element.tag in error_tag_dict:
            for error in error_tag_dict[element.tag]:
                if error.needs_path() and not installer_is_path:
                    continue

                if error.check(installer_trees[1].getroot(),
                               element,
                               installer):
                    error_msg = error.error_string()
                    checked_errors.append((element.sourceline,
                                           error.title(),
                                           error_msg.format(element.tag),
                                           element.tag))

    return checked_errors
