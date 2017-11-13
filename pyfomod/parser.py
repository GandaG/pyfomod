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

from pyfomod import tree


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
        return None


class _FomodLookup(etree.PythonElementClassLookup):
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


FOMOD_PARSER = etree.XMLParser(remove_blank_text=True)
FOMOD_PARSER.set_element_class_lookup(_SpecialLookup(_FomodLookup()))
