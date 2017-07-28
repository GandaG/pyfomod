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
This module holds the custom parser and the key classes necessary
for the api.
"""

import os

from lxml import etree

from .io import get_installer_files


class FomodElement(etree.ElementBase):
    """
    The base class for all FOMOD elements. This, along with the lxml API,
    serves as the low-level API for pyfomod.
    """
    pass


class Root(FomodElement):
    """
    This class is used with the 'config' tag.

    It provides access to all values from the 'info.xml' file via properties
    as well as high-level functions and properties to read and modify the
    'ModuleConfig.xml' file.
    """
    pass


class InstallPattern(FomodElement):
    """
    This class is used with the 'pattern' tag under
    'conditionalFileInstalls'.

    It provides access to each pattern's files to be installed
    as well as the corresponding dependency network.
    """
    pass


class Dependencies(FomodElement):
    """
    This class is used with the 'dependencies', 'visible', and
    'moduleDependencies' tags.

    It provides access to a dependencies network. The truth value
    of this class is influenced by its dependency type ('And' or 'Or')
    and by its actual dependencies.
    """
    pass


class InstallStep(FomodElement):
    """
    This class is used with the 'installStep' tag.

    Provides access to a single install step.
    """
    pass


class Group(FomodElement):
    """
    This class is used with the 'group' tag.

    Provides access to a plugin group within an install step.
    """
    pass


class Plugin(FomodElement):
    """
    This class is used with the 'plugin' tag.

    Provides access to a singular plugin and its properties.
    """
    pass


class TypeDependency(FomodElement):
    """
    This class is used with the 'dependencyType' tag.

    Provides access to a list of patterns that determine the
    plugin's type, based on dependencies.
    """
    pass


class TypePattern(FomodElement):
    """
    This class is use with the 'pattern' tag under 'dependencyType'.

    Provides access to a dependency network and the type it sets.
    """
    pass


class _SpecialLookup(etree.CustomElementClassLookup):
    """
    This class is used to lookup and filter outcomments an PI's before we
    get to the tree-based lookup because it REALLY doesn't like to lookup
    comments.
    """
    def lookup(self, node_type, doc, ns, name):
        del doc, ns, name

        if node_type == "comment":
            return etree.CommentBase
        elif node_type == "PI":
            return etree.PIBase
        else:
            return None


class _FomodLookup(etree.PythonElementClassLookup):
    """
    The class used to lookup the correct class for key tags in the FOMOD
    document. A full tree based lookup is necessary due to the two pattern
    classes having the same tag name but being essentially different.
    """
    def lookup(self, doc, element):
        del doc  # make pylint shut up

        element_class = FomodElement
        if element.tag == 'config':
            element_class = Root
        elif element.tag in ('dependencies', 'moduleDependencies', 'visible'):
            element_class = Dependencies
        elif element.tag == 'installStep':
            element_class = InstallStep
        elif element.tag == 'group':
            element_class = Group
        elif element.tag == 'plugin':
            element_class = Plugin
        elif element.tag == 'dependencyType':
            element_class = TypeDependency

        # the pattern classes
        # ugh...
        else:
            for child in element:
                if child.tag == 'type':  # the typepattern has a type child
                    element_class = TypePattern
                elif child.tag == 'files':  # and installpattern a files child
                    element_class = InstallPattern

        return element_class


FOMOD_PARSER = etree.XMLParser(remove_blank_text=True)
FOMOD_PARSER.set_element_class_lookup(_SpecialLookup(_FomodLookup()))
INFO_SCHEMA = etree.XMLSchema(etree.parse(
    os.path.join(os.path.dirname(__file__), 'info.xsd')).getroot())
CONF_SCHEMA = etree.XMLSchema(etree.parse(
    os.path.join(os.path.dirname(__file__), 'conf.xsd')).getroot())


def validate_installer(installer):
    """
    Returns a boolean, True if the installer is valid, False if not.

    Accepts as arguments a parsed Root object, a tuple or list of
    two parsed lxml trees (info and config, in that order) or a valid
    path to an installer. The path follows the same rules as when given
    to get_installer_files.

    Raises ValueError if the argument passed does not comply with the
    rules above.
    """
    # the variable to hold the info and config trees
    installer_trees = None

    # check if it's a parsed Root object - dead end for now
    if isinstance(installer, Root):
        raise NotImplementedError

    # checks if it's a tuple of parsed lxml trees
    if isinstance(installer, tuple) or isinstance(installer, list):
        try:
            installer_trees = (etree.ElementTree(installer[0].getroot()),
                               etree.ElementTree(installer[1].getroot()))
        except AttributeError:
            installer_trees = tuple(installer)

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
