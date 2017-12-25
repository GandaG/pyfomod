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
This module holds the custom parser.
"""

from lxml import etree
from pyfomod import io, tree, validation


def new(old_schema_link=True):
    """
    Creates a brand new fomod installer.

    Args:
        old_schema_link (bool, optional): Whether to use the old schema
            location for compatibility with some mod managers.

    Returns:
        tree.Root: The root of the new fomod tree.
    """
    if old_schema_link:
        namespace = 'http://qconsulting.ca/fo3/ModConfig5.0.xsd'
    else:
        namespace = "https://github.com/fomod-lang/fomod/blob/" \
                    "5.0/ModuleConfig.xsd"
    attribs = {"{http://www.w3.org/2001/XMLSchema-instance}"
               "noNamespaceSchemaLocation": namespace}

    fake_parser = etree.XMLParser(remove_blank_text=True)
    fake_parser.set_element_class_lookup(SpecialLookup(FomodLookup()))

    info_tree = fake_parser.makeelement('fomod')
    info_tree._setup_new_element()
    validation.assert_valid(info_tree)

    parser = FomodParser(info_tree, remove_blank_text=True)
    parser.set_element_class_lookup(SpecialLookup(FomodLookup()))

    conf_tree = parser.makeelement('config', attrib=attribs)
    conf_tree._setup_new_element()
    validation.assert_valid(conf_tree)

    return conf_tree


def from_string(info, conf):
    """
    Accepts strings (or bytestrings) as the fomod xml trees and returns
    a Root object.

    ``info`` corresponds to the contents of the *info.xml* file.
    ``conf`` corresponds to the contents of the *ModuleConfig.xml* file.

    Args:
        info (str, bytes): The contents of the *info.xml* file.
        conf (str, bytes): The contents of the *ModuleConfig.xml* file.

    Returns:
        tree.Root: The Root of the fomod installer.

    Raises:
        AssertionError: If the strings do not contain valid fomod xml.
    """
    # the fake parser will be used to get correct element types
    # during tree builder
    fake_parser = etree.XMLParser(remove_blank_text=True)
    fake_parser.set_element_class_lookup(SpecialLookup(FomodLookup()))

    info_tree = etree.fromstring(info, parser=fake_parser)
    validation.assert_valid(info_tree)

    parser = FomodParser(info_tree, remove_blank_text=True)
    parser.set_element_class_lookup(SpecialLookup(FomodLookup()))

    conf_tree = etree.fromstring(conf, parser=parser)
    validation.assert_valid(conf_tree)

    return conf_tree


def parse(source):
    """
    Accepts paths to the fomod package and returns a Root object.

    Args:
        source (str, list(str, str), tuple(str, str)):
            The path to the fomod package. Accepts a single folder path
            or a tuple/list of file paths as *(info.xml, ModuleConfig.xml)*.

            The single path must point to a folder with the following rules.
            Both a subfolder named *fomod* in the `path` and
            `path` itself being the *fomod* folder are supported.
            Priority is given to *fomod* subfolder.
            `path`. Examples:

            * `folder/somefolder/` - *somefolder* contains a *fomod* subfolder;
            * `folder/somefolder/fomod`.

    Returns:
        tree.Root: The Root of the fomod installer.

    Raises:
        AssertionError: If the strings do not contain valid fomod xml.
    """
    if not isinstance(source, (tuple, list)):
        source = io.get_installer_files(source)

    with open(source[0], 'rb') as info, open(source[1], 'rb') as conf:
        return from_string(info.read(), conf.read())


def to_string(fomod):
    """
    Serializes a fomod installer ``fomod`` to a tuple of bytestrings,
    (*info.xml*, *ModuleConfig.xml*).

    Args:
        fomod (tree.Root): The installer to serialize.

    Returns:
        tuple(bytes, bytes): A tuple of bytestrings as
            (*info.xml*, *ModuleConfig.xml*)

    Raises:
        AssertionError: If the strings do not contain valid fomod xml.
    """
    info_tree = etree.ElementTree(fomod.info_root)
    validation.assert_valid(info_tree)
    info_str = etree.tostring(info_tree,
                              xml_declaration=True,
                              pretty_print=True,
                              encoding='utf-8')

    conf_tree = etree.ElementTree(fomod)
    validation.assert_valid(conf_tree)
    conf_str = etree.tostring(conf_tree,
                              xml_declaration=True,
                              pretty_print=True,
                              encoding='utf-8')

    return info_str, conf_str


def write(fomod, path):
    """
    Writes a fomod installer ``fomod`` to a package at ``path``. Folders and
    files are created as necessary.

    Args:
        fomod (tree.Root): The installer to serialize.
        path (str, tuple(str, str), list(str, str): The path to write to.
            Accepts a single folder path
            or a tuple/list of file paths as *(info.xml, ModuleConfig.xml)*.

            The single path must point to a folder with the following rules.
            Both a subfolder named *fomod* in the `path` and
            `path` itself being the *fomod* folder are supported.
            Priority is given to *fomod* subfolder.
            `path`. Examples:

            - `folder/somefolder/` - a *fomod* folder will be created
              in *somefolder* if needed;
            - `folder/somefolder/fomod`.

    Raises:
        AssertionError: If the strings do not contain valid fomod xml.
    """
    if not isinstance(path, (tuple, list)):
        path = io.get_installer_files(path, create_missing=True)

    with open(path[0], 'wb') as info, open(path[1], 'wb') as conf:
        info_str, conf_str = to_string(fomod)
        info.write(info_str)
        conf.write(conf_str)


class SpecialLookup(etree.CustomElementClassLookup):
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
        return None


class FomodLookup(etree.PythonElementClassLookup):
    """
    The class used to lookup the correct class for key tags in the FOMOD
    document. A full tree based lookup is necessary due to the two pattern
    classes having the same tag name but being essentially different.
    """
    def lookup(self, doc, element):
        del doc  # make pylint shut up

        element_class = tree.FomodElement

        if element.tag == 'config':
            element_class = tree.Root
        elif element.tag in ('dependencies', 'moduleDependencies', 'visible'):
            element_class = tree.Dependencies
        elif element.tag == 'installStep':
            element_class = tree.InstallStep
        elif element.tag == 'group':
            element_class = tree.Group
        elif element.tag == 'plugin':
            element_class = tree.Plugin
        elif element.tag == 'dependencyType':
            element_class = tree.TypeDependency

        # the pattern classes
        # ugh...
        elif element.tag == 'pattern':
            grandparent = element.getparent().getparent()
            if grandparent.tag == "conditionalFileInstalls":
                element_class = tree.InstallPattern
            elif grandparent.tag == "dependencyType":
                element_class = tree.TypePattern

        return element_class


class FomodParser(etree.XMLParser):
    """
    Currently used exclusively for holding package-global variables
    for the trees. Fun.
    """
    def __init__(self, info_root, *args, **kwargs):
        self.info_root = info_root
        super(FomodParser, self).__init__(*args, **kwargs)
