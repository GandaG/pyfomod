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

from collections import namedtuple
from copy import deepcopy

from lxml import etree

import pyfomod

from .exceptions import InvalidArgument
from .schema import (copy_schema, get_attribute_type, get_builtin_value,
                     get_complex_type, get_doc_text, get_max_occurs,
                     get_min_occurs, get_order_from_elem, get_order_from_group,
                     get_order_from_type, is_builtin_attribute,
                     is_complex_element, localname)

_Attribute = namedtuple('_Attribute', "name doc default type use restriction")
"""
This ``namedtuple`` represents a single possible attribute for a FomodElement.

Attributes:
    name (str): The identifier of this attribute.
    doc (str): The schema documentation for this attribute.
    default (str or None): The default value for this attribute or None if
        none is specified.
    type (str): The type of this attribute's value.
    use (str): Either ``'optional'``, ``'required'`` or ``'prohibited'``.
    restriction (_AttrRestriction): A namedtuple with the attribute's
        restrictions. For more info refer to :py:class:`_AttrRestriction`.
"""

_ATTR_REST_ATTRIBUTES = "type enum_list decimals length max_exc max_inc " \
                        "max_len min_exc min_inc min_len pattern total_digits"
_AttrRestriction = namedtuple('_AttrRestriction', _ATTR_REST_ATTRIBUTES)
"""
This ``namedtuple`` represents a single attribute's value restrictions.
For more information about restrictions refer to `W3Schools`_.

.. _W3Schools: https://www.w3schools.com/xml/schema_facets.asp

Attributes:
    type (str): A string containing all restriction types separated by a
        single whitespace. Example: ``'max_length min_length '``
    enum_list (list(_AttrRestElement)): A list of possible values for this
        attribute.

Warning:
    Since none of the other restriction types occur in the actual schemas
    all other attributes are always set to :py:class:`None`.
"""

_AttrRestElement = namedtuple('_AttrRestElement', 'value doc')
"""
This ``namedtuple`` represents a single value for a restriction.

Attributes:
    value (str): The string containing the value.
    doc (str): The schema documentation for this value.
"""

_ORDER_INDICATOR_ATTRIBUTES = 'type element_list max_occ min_occ'
_OrderIndicator = namedtuple('_OrderIndicator', _ORDER_INDICATOR_ATTRIBUTES)
"""
This ``namedtuple`` represents an order indicator in the element's schema.
For more information about order indicators refer to `W3Schools`_.

.. _W3Schools: https://www.w3schools.com/xml/schema_facets.asp

Attributes:
    type (str): Either ``'sequence'``, ``'choice'`` or ``'all'``.
    element_list (list): A list of :py:class:`_OrderIndicator` and
        :py:class:`_ChildElement` that translates an order of valid children.
    max_occ (int): The maximum number of times this order can occur in a row.
    min_occ (int): The minimum number of times this order can occur in a row.
"""

_ChildElement = namedtuple('_ChildElement', 'tag max_occ min_occ')
"""
This ``namedtuple`` represents a valid child of an element.

Attributes:
    tag (str): The tag of the possible child.
    max_occ (int): The maximum number of times this child can occur in a row.
    min_occ (int): The minimum number of times this child can occur in a row.
"""


class FomodElement(etree.ElementBase):
    """
    The base class for all FOMOD elements. This, along with the lxml API,
    serves as the low-level API for pyfomod.

    Attributes:
        _schema (lxml.etree._Element): The schema this element belongs to.
        _schema_element (lxml.etree._Element): The element in the schema this
            element corresponds to.
        _schema_type (lxml.etree._Element): The type that corresponds to
            `_schema_element`. Usually this will be a *complexType* but can be
            the same as `_schema_element` if it's a simple element.
    """

    @property
    def max_occurences(self):
        """
        int or None:
            Returns the maximum times this element can be
            repeated or ``None`` if there is no limit.
        """
        return get_max_occurs(self._schema_element)

    @property
    def min_occurences(self):
        """
        int:
            Returns the minimum times this element has to be repeated.
        """
        return int(self._schema_element.get('minOccurs', 1))

    @property
    def type(self):
        """
        str or None:
            The text type of this element. :py:class:`None` if no text is
            allowed.
        """
        if not is_complex_element(self._schema_element):
            return self._schema_element.get('type')[3:]

        base_exp = ("*[local-name()='simpleContent']/"
                    "*[local-name()='extension'] | "
                    "*[local-name()='simpleContent']/"
                    "*[local-name()='restriction']")
        try:
            schema_type = get_complex_type(self._schema_element)
            base_elem = schema_type.xpath(base_exp)[0]
            return get_builtin_value(base_elem.get('base'))
        except IndexError:
            return None

    @property
    def comment(self):
        """
        str:
            The text of this element' comment.
            If no comment exists when setting new text, a comment is created.
            If this is set to :class:`None` the comment is deleted.
        """
        if self._comment is None:
            return ""
        return self._comment.text

    @comment.setter
    def comment(self, text):
        if self._comment is None:
            if text is None:
                return
            self.addprevious(etree.Comment(text))

            # pylint: disable=attribute-defined-outside-init
            self._comment = self.getprevious()
        elif text is None:
            if self.getparent() is not None:
                self.getparent().remove(self._comment)
            # if comment is at top level then just make it None,
            # makes no difference
            self._comment.text = None
            # pylint: disable=attribute-defined-outside-init
            # this is needed to lose the reference to the comment.
            self._comment = None
        else:
            self._comment.text = text

    @property
    def doc(self):
        """
        str:
            Returns the documentation text associated with this element
            in the schema.
        """
        doc = get_doc_text(self._schema_element)
        if doc is None:
            return ""
        return doc

    @classmethod
    def _copy_element(cls, element, copy_level=0):
        copy = etree.Element(element.tag,
                             attrib=element.attrib,
                             nsmap=element.nsmap)
        copy.text = element.text
        copy.tail = element.tail

        if copy_level != 0:
            for child in element:
                copy.append(cls._copy_element(child, copy_level - 1))

        return copy

    @classmethod
    def _valid_children_parse_order(cls, ord_elem):
        """
        Parses the *ord_elem* order indicator.
        Needs to be separate from the main method to be recurrent.
        Returns an _OrderIndicator named tuple for the *ord_elem*.
        """
        child_list = []

        for child in ord_elem:
            child_tuple = None
            if localname(child) == 'element':
                child_tuple = _ChildElement(child.get('name'),
                                            get_max_occurs(child),
                                            get_min_occurs(child))
            elif localname(child) == 'any':
                child_tuple = _ChildElement(None,
                                            get_max_occurs(child),
                                            get_min_occurs(child))
            elif localname(child) == 'group':
                child_order = get_order_from_group(child)
                child_tuple = cls._valid_children_parse_order(child_order)
            else:
                child_tuple = cls._valid_children_parse_order(child)
            child_list.append(child_tuple)

        return _OrderIndicator(localname(ord_elem), child_list,
                               get_max_occurs(ord_elem),
                               get_min_occurs(ord_elem))

    def _init(self):
        """
        Used to setup the class, instead of an __init__
        since lxml doesn't let us use it.
        """
        # pylint: disable=attribute-defined-outside-init

        # the schema this element belongs to
        self._schema = pyfomod.FOMOD_SCHEMA_TREE

        # the element that holds minOccurs, etc.
        self._schema_element = self._lookup_element()

        # the comment associated with this element.
        # this comment always exists before the element.
        self._comment = None
        if (self.getprevious() is not None and
                self.getprevious().tag is etree.Comment):
            self._comment = self.getprevious()

    def _lookup_element(self):
        """
        Looks up the corresponding element/complexType in the corresponding
        schema. Serves as base for all other lookups.
        """
        ancestor_list = list(self.iterancestors())[::-1]
        ancestor_list.append(self)

        # the current element will always be an actual element
        # it will contain tag, minOccurs, maxOccurs, etc.
        current_element = None

        # the current type in schema
        # in most cases it will actually be a complexType
        current_type = self._schema

        for elem in ancestor_list:
            xpath_exp = "{*}element[@name=\"" + elem.tag + "\"]"
            current_element = current_type.find(xpath_exp)

            # this means there could order tags and/or be nested in a group tag
            if current_element is None:
                order_elem = get_order_from_type(current_type)
                current_element = order_elem.find(".//" + xpath_exp)
                if current_element is None:
                    raise AssertionError("No element was found for this tag.")

            current_type = get_complex_type(current_element)
            if current_type is None:
                current_type = current_element

        return current_element

    def valid_attributes(self):
        """
        Gets all possible attributes of this element
        along with some extra info in the
        :py:class:`namedtuple <collections.namedtuple>`.

        Returns:
            list(_Attribute):
                A list of all possible attributes
                this element can have. For more info refer to
                :py:class:`_Attribute`.
        """
        if not is_complex_element(self._schema_element):
            return []

        result_list = []
        attr_exp = ("*[local-name()='attribute'] | "
                    "*[local-name()='simpleContent']/"
                    "*[local-name()='extension']/"
                    "*[local-name()='attribute'] | "
                    "*[local-name()='simpleContent']/"
                    "*[local-name()='restriction']/"
                    "*[local-name()='attribute']")

        schema_type = get_complex_type(self._schema_element)
        attr_list = schema_type.xpath(attr_exp)

        for attr in attr_list:
            name = attr.get('name')
            doc = get_doc_text(attr)
            default = attr.get('default')
            use = attr.get('use', 'optional')
            attr_type = attr.get('type')
            restriction = None

            if is_builtin_attribute(attr):
                attr_type = get_builtin_value(attr_type)
            else:
                simple_type = get_attribute_type(attr)
                # restriction is guaranteed
                rest_elem = simple_type.find('{*}restriction')

                attr_type = get_builtin_value(rest_elem.get('base'))
                if attr_type is None:
                    attr_type = rest_elem.get('base')
                rest_type = ''
                enum_list = []

                for child in rest_elem:
                    doc_child = get_doc_text(child)
                    value = child.get('value')

                    rest_tuple = _AttrRestElement(value, doc_child)

                    if localname(child) == 'enumeration':
                        if 'enumeration' not in rest_type:
                            rest_type += 'enumeration '
                        enum_list.append(rest_tuple)

                restriction = _AttrRestriction(rest_type, enum_list, None,
                                               None, None, None,
                                               None, None, None,
                                               None, None, None)

            result_list.append(_Attribute(name, doc, default, attr_type,
                                          use, restriction))

        return result_list

    def required_attributes(self):
        """
        Utility method that returns only attributes that are required
        by this element.

        Returns:
            list(_Attribute): The list of required attributes.
        """
        valid_attrib = self.valid_attributes()
        return [attr for attr in valid_attrib if attr.use == 'required']

    def _find_valid_attribute(self, name):
        """
        Checks if possible attribute name is possible within the schema.
        Returns the _Attribute namedtuple for the possible attribute.
        If there is no possible attribute, raises InvalidArgument.
        """
        valid_attrs = self.valid_attributes()
        possible_attr = None
        for attr in valid_attrs:
            if attr.name == name:
                possible_attr = attr
                break

        if possible_attr is None:
            raise InvalidArgument()
        else:
            return possible_attr

    def get_attribute(self, name):
        """
        Args:
            name (str): The attribute's name.

        Returns:
            The attribute's value.

        Raises:
            InvalidArgument: If the attribute is not allowed by the schema.
        """
        existing_attr = self.get(name)
        if existing_attr is not None:
            return existing_attr

        default_attr = self._find_valid_attribute(name)
        if default_attr.default is not None:
            return default_attr.default
        return ""

    def set_attribute(self, name, value):
        """
        Args:
            name (str): The attribute's name.
            value (str): The attribute's value.

        Raises:
            ValueError: If the value is not allowed by the attribute's
                restrictions.
            InvalidArgument: If the attribute is not allowed by the schema.
        """
        possible_attr = self._find_valid_attribute(name)
        if possible_attr.restriction is not None:
            if 'enumeration' in possible_attr.restriction.type:
                enum_list = possible_attr.restriction.enum_list
                if value not in [enum.value for enum in enum_list]:
                    raise ValueError("{} is not allowed by this "
                                     "attribute's restrictions.".format(value))

        self.set(name, value)

    def valid_children(self):
        """
        Gets all the possible, valid children for this element.

        Returns:
            _OrderIndicator or None:
                This :py:class:`namedtuple <collections.namedtuple>` contains
                the valid children for this element. For more information on
                its structure refer to :py:class:`_OrderIndicator`.
                `None` if this element has no valid children.
        """
        order_elem = get_order_from_elem(self._schema_element)
        if order_elem is None:
            return None

        return self._valid_children_parse_order(order_elem)

    def _required_children_choice(self, choice):
        """
        Returns the required children of a choice order indicator.
        Always selects the first path in the choice, regardless of
        the actual children.
        It's probably a good idea to eventually try to make it choose
        the corrent path based on the existing children.
        """
        req_child = []
        try:
            selected_path = choice.element_list[0]
        except IndexError:
            return []

        if isinstance(selected_path, _OrderIndicator):
            if selected_path.type == 'choice':
                req_child.extend(self._required_children_choice(selected_path))
            else:
                req_child.extend(
                    self._required_children_sequence(selected_path))
        elif selected_path.min_occ > 0:
            req_child.append((selected_path.tag, selected_path.min_occ))

        for index in range(0, len(req_child)):
            req_child[index] = (req_child[index][0],
                                req_child[index][1] * choice.min_occ)

        return req_child

    def _required_children_sequence(self, sequence):
        """
        Returns the required children of a sequence order indicator.
        """
        req_child = []

        for elem in sequence.element_list:
            if isinstance(elem, _OrderIndicator):
                if elem.type == 'choice':
                    req_child.extend(self._required_children_choice(elem))
                else:
                    req_child.extend(self._required_children_sequence(elem))
            elif elem.min_occ > 0:
                req_child.append((elem.tag, elem.min_occ))

        for index in range(0, len(req_child)):
            req_child[index] = (req_child[index][0],
                                req_child[index][1] * sequence.min_occ)

        return req_child

    def required_children(self):
        """
        Returns a list with the required children by this element.
        Currently, this assumes no children exist and whenever there
        is a choice to be made it always chooses the first path.

        Returns:
            list(tuple(string, int)): A list of tuples as
                (child tag, child minimum occurences).
        """
        valid_children = self.valid_children()
        if valid_children is None:
            return []
        elif valid_children.type == 'choice':
            return self._required_children_choice(valid_children)
        return self._required_children_sequence(valid_children)

    def _find_possible_index(self, tag):
        """
        Tries to figure out if a child can be added to this element,
        and if it can, what index it should be inserted at.

        To this end, a shallow copy of this element's schema correspondence
        and it's possible children is performed.
        After, the same is done to this element and it's real children.
        A test element with the child's tag is created.
        This test element is then inserted at every possible position in the
        copy of self (reversed order) until a valid position is found.
        """
        schema_elem = copy_schema(self._schema_element,
                                  copy_level=1, rm_attr=True)
        self_copy = self._copy_element(self, copy_level=1)

        test_elem = etree.Element(tag)
        schema = etree.XMLSchema(schema_elem)

        self_copy.append(test_elem)
        if schema.validate(self_copy):
            return -1

        for index in reversed(range(len(self_copy))):
            self_copy.insert(index, test_elem)
            if schema.validate(self_copy):
                return index

        return None

    def can_add_child(self, child):
        """
        Checks if a given child can be possibly added to this element.

        Args:
            child (str or FomodElement): The tag or the actual child to add.

        Returns:
            bool: Whether the child can be added or not.

        Raises:
            TypeError: If child is neither a string nor FomodElement.

        Warning:
            This method and its corresponding :func:`~FomodElement.add_child`
            can both possibly be performance heavy on elements with large
            numbers of children.

            It is therefore recommended to use this pattern::

                from pyfomod.exceptions import InvalidArgument

                try:
                    element.add_child(child)
                except InvalidArgument:
                    pass

            Instead of::

                if element.can_add_child(child):
                    element.add_child(child)
        """
        tag = ""
        if isinstance(child, str):
            tag = child
        elif isinstance(child, FomodElement):
            tag = child.tag
            parent = child.getparent()
            if parent is not None and not parent.can_remove_child(child):
                return False
        else:
            raise TypeError("Only tags (string) and elements (FomodElement)"
                            " are accepted as arguments.")

        if self._find_possible_index(tag) is None:
            return False
        return True

    def _setup_new_element(self):
        """
        Sets up a newly created element (self) by adding the required
        attributes and any required children (bypass validation checks).
        """
        for attr in self.required_attributes():
            if attr.default is not None:
                self.set_attribute(attr.name, attr.default)
            elif (attr.restriction is not None and
                  'enumeration' in attr.restriction.type):
                self.set_attribute(attr.name,
                                   attr.restriction.enum_list[0].value)
            else:
                self.set_attribute(attr.name, '')

        for elem in self.required_children():
            for _ in range(0, elem[1]):
                child = etree.SubElement(self, elem[0])
                child._setup_new_element()

    def add_child(self, child):
        """
        Adds a child to this element.

        If *child* is a :class:`FomodElement` and it has a parent element then
        it is first removed using :func:`~FomodElement.remove_child`.

        Args:
            child (str or FomodElement): The tag or the actual child to add.

        Raises:
            TypeError: If child is neither a string nor FomodElement.
            InvalidArgument: If the child cannot be added to this element.
        """
        tag = ""
        child_is_tag = False
        if isinstance(child, str):
            tag = child
            child_is_tag = True
        elif isinstance(child, FomodElement):
            tag = child.tag
        else:
            raise TypeError("Only tags (string) and elements (FomodElement)"
                            " are accepted as arguments.")

        index = self._find_possible_index(tag)
        if index is None:
            raise InvalidArgument()

        if child_is_tag:
            child = etree.SubElement(self, tag)
            child._setup_new_element()
        else:
            parent = child.getparent()
            if parent is not None:
                parent.remove_child(child)
        self.insert(index, child)
        if child._comment is not None:
            self.insert(index, child._comment)

    def can_remove_child(self, child):
        """
        Checks if a given child can be removed while maintaining validity.

        Args:
            child (FomodElement): The child element to remove.

        Returns:
            bool: Whether the child can be removed.

        Raises:
            TypeError: If child is not a FomodElement.
            ValueError: If child is not a child of this element.
        """
        if not isinstance(child, FomodElement):
            raise TypeError("child argument must be a FomodElement.")
        elif child not in self:
            raise ValueError("child argument is not a child of this element.")

        index = self.index(child)
        schema_elem = copy_schema(self._schema_element,
                                  copy_level=1, rm_attr=True)
        self_copy = self._copy_element(self, copy_level=1)
        self_copy.remove(self_copy[index])
        schema = etree.XMLSchema(schema_elem)
        return schema.validate(self_copy)

    def remove_child(self, child):
        """
        Removes a child from this element.

        Args:
            child (FomodElement): The child element to remove.

        Raises:
            TypeError: If child is not a FomodElement.
            ValueError: If child is not a child of this element.
            InvalidArgument: If child cannot be removed from this element.
        """
        if self.can_remove_child(child):
            if child._comment is not None:
                self.remove(child._comment)
            self.remove(child)
        else:
            raise InvalidArgument()

    def can_replace_child(self, old_child, new_child):
        """
        Checks if a given child can be replaced while maintaining validity.

        Args:
            old_child (FomodElement): The child element to replace.
            new_child (FomodElement): The child element to insert.

        Returns:
            bool: Whether the child can be replaced.

        Raises:
            TypeError: If either argument is not a FomodElement.
            ValueError: If old_child is not a child of this element.
        """
        if not (isinstance(old_child, FomodElement) or
                isinstance(new_child, FomodElement)):
            raise TypeError("child arguments must be a FomodElement.")
        elif old_child not in self:
            raise ValueError("child argument is not a child of this element.")

        parent = new_child.getparent()
        if parent is not None and not parent.can_remove_child(new_child):
            return False
        index = self.index(old_child)
        schema_elem = copy_schema(self._schema_element,
                                  copy_level=1, rm_attr=True)
        self_copy = self._copy_element(self, copy_level=1)
        self_copy.replace(self_copy[index], etree.Element(new_child.tag))
        schema = etree.XMLSchema(schema_elem)
        return schema.validate(self_copy)

    def replace_child(self, old_child, new_child):
        """
        Replaces *old_child* with *new_child*.

        If *new_child* is a :class:`FomodElement` and it has a parent element
        then it is first removed using :func:`~FomodElement.remove_child`.

        Args:
            old_child (FomodElement): The child element to replace.
            new_child (FomodElement): The child element to insert.

        Raises:
            TypeError: If either argument is not a FomodElement.
            ValueError: If old_child is not a child of this element.
            InvalidArgument: If old_child can't be replaced by new_child.
        """
        if self.can_replace_child(old_child, new_child):
            parent = new_child.getparent()
            if parent is not None:
                parent.remove_child(new_child)
            index = self.index(old_child)
            if old_child._comment is not None:
                self.remove(old_child._comment)
            if new_child._comment is not None:
                self.insert(index, new_child._comment)
            self.replace(old_child, new_child)
        else:
            raise InvalidArgument()

    def __copy__(self):
        return self.__deepcopy__(None)

    def __deepcopy__(self, memo):
        parent = self.getparent()
        if parent is None:
            copy_elem = self.makeelement(self.tag,
                                         attrib=self.attrib,
                                         nsmap=self.nsmap)
        else:
            copy_elem = etree.SubElement(parent,
                                         self.tag,
                                         attrib=self.attrib,
                                         nsmap=self.nsmap)
            parent.remove(copy_elem)

        copy_elem._comment = deepcopy(self._comment)
        copy_elem.text = self.text
        copy_elem.tail = self.tail

        for child in self:
            copy_elem.append(deepcopy(child))

        return copy_elem


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
        elif element.tag == 'pattern':
            grandparent = element.getparent().getparent()
            if grandparent.tag == "conditionalFileInstalls":
                element_class = InstallPattern
            elif grandparent.tag == "dependencyType":
                element_class = TypePattern

        return element_class


FOMOD_PARSER = etree.XMLParser(remove_blank_text=True)
FOMOD_PARSER.set_element_class_lookup(_SpecialLookup(_FomodLookup()))
