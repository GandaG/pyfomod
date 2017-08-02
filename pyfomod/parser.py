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


from lxml import etree


class FomodElement(etree.ElementBase):
    """
    The base class for all FOMOD elements. This, along with the lxml API,
    serves as the low-level API for pyfomod.
    """

    def _setup(self, schema):
        """
        Used to setup the class, instead of an __init__
        since lxml doesn't let us use it.
        """
        # pylint: disable=attribute-defined-outside-init

        # the schema this element belongs to
        self.schema = schema

        # the element that holds minOccurs, etc.
        self.schema_element = None

        # the type of this element (can be the same as the schema_element)
        # holds info about attributes, children, etc.
        self.schema_type = None

    @staticmethod
    def compare(elem1, elem2, recursive=False):
        """
        Compares *elem1* with *elem2*.

        Returns a boolean.
        """
        if (elem1.tag != elem2.tag or
                elem1.text != elem2.text or
                elem1.tail != elem2.tail or
                elem1.attrib != elem2.attrib):
            return False
        if not recursive:
            return True
        if len(elem1) != len(elem2):
            return False
        return all(elem1.compare(c1, c2) for c1, c2 in zip(elem1, elem2))

    def _lookup_element(self):
        """
        Looks up the corresponding element/complexType in the corresponding
        schema. Serves as base for all otther lookups.
        """
        ancestor_list = list(self.iterancestors())[::-1]
        ancestor_list.append(self)
        nsmap = '{' + self.schema.nsmap['xs'] + '}'

        # the current element in schema
        # in most cases it will actually be a complexType
        current_element = self.schema

        # the holder element will always be an actual element
        # it will contain tag, minOccurs, maxOccurs, etc.
        holder_element = None

        for elem in ancestor_list:
            xpath_exp = "{}element[@name=\"{}\"]".format(nsmap, elem.tag)
            holder_element = current_element.find(xpath_exp)

            # this just means there is an order tag between current and next
            if holder_element is None:
                ord_exp = "xs:all | xs:sequence | xs:choice"
                temp = current_element.xpath(ord_exp,
                                             namespaces=self.schema.nsmap)
                holder_element = temp[0].find(xpath_exp)

            # a complexType that is used solely for this element
            if holder_element.get('type') is None:
                complex_exp = '{}complexType'.format(nsmap)
                current_element = holder_element.find(complex_exp)

            # it is vital that this is the last element
            # if not, then the xml is not valid and something is wrong
            # with this code
            elif holder_element.get('type').startswith('xs:'):
                current_element = holder_element

            # last, the complex type is separate from the holder element
            else:
                custom_type = holder_element.get('type')
                complx_exp = '{}complexType[@name=\"{}\"]'.format(nsmap,
                                                                  custom_type)
                current_element = self.schema.find(complx_exp)

            # pylint: disable=attribute-defined-outside-init
            self.schema_element = holder_element
            self.schema_type = current_element


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
