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
This module holds the utility functions necessary for handling the schema.
"""

from copy import deepcopy

from lxml import etree

BUILTIN_TYPES = ['decimal',
                 'float',
                 'double',
                 'integer',
                 'positiveInteger',
                 'negativeInteger',
                 'nonPositiveInteger',
                 'nonNegativeInteger',
                 'long',
                 'int',
                 'short',
                 'byte',
                 'unsignedLong',
                 'unsignedInt',
                 'unsignedShort',
                 'unsignedByte',
                 'dateTime',
                 'date',
                 'gYearMonth',
                 'gYear',
                 'duration',
                 'gMonthDay',
                 'gDay',
                 'gMonth',
                 'string',
                 'normalizedString',
                 'token',
                 'language',
                 'NMTOKEN',
                 'NMTOKENS',
                 'Name',
                 'NCName',
                 'ID',
                 'IDREFS',
                 'ENTITY',
                 'ENTITIES',
                 'QName',
                 'boolean',
                 'hexBinary',
                 'base64Binary',
                 'anyURI',
                 'notation']


def localname(element):
    """Returns a namespace-free tag for ``element``."""
    return etree.QName(element).localname


def get_root(element):
    """Returns the root element of the tree ``element`` is in."""
    return element.getroottree().getroot()


def get_min_occurs(element):
    """Returns the minimum occurences for ``element``."""
    return int(element.get('minOccurs', 1))


def get_max_occurs(element):
    """Returns maxOccurs for ``element``. None if unbounded."""
    max_occ = element.get('maxOccurs', 1)
    if max_occ == 'unbounded':
        return None
    return int(max_occ)


def get_doc_text(element):
    """
    Returns the text of the of the annotation/documentation element
    below the ``element``. Example::

        <``element``>
            <annotation>
                <documentation>
                    This method returns this text.
                </documentation>
            </annotation>
        </``element``>

    If no such structure could be found, returns ``None``.
    """
    doc_elem = element.find("{*}annotation/{*}documentation")
    if doc_elem is not None:
        return doc_elem.text
    return None


def get_order_elem(container):
    """Returns the order indicator element child of ``container``."""
    ord_exp = "*[local-name()='all'] | " \
              "*[local-name()='sequence'] | " \
              "*[local-name()='choice']"
    try:
        return container.xpath(ord_exp)[0]
    except IndexError:
        return None


def get_group_ref(element):
    """Returns the group reference child of ``element``."""
    return element.find('{*}group[@ref]')


def has_group_ref(element):
    """Checks whether ``element`` contains a group reference."""
    if get_group_ref(element) is not None:
        return True
    return False


def get_group_elem(group_ref):
    """Grabs the group element from ``group_ref``."""
    group_elem_exp = "{*}group[@name=\"" + group_ref.get('ref') + "\"]"
    return get_root(group_ref).find(group_elem_exp)


def get_builtin_value(value):
    """
    If ``value`` is in a namespace, returns the value without namespace.
    Otherwise returns None.
    """
    split = value.split(':', maxsplit=1)
    if len(split) > 1 and split[1] in BUILTIN_TYPES:
        return split[1]
    return None


def get_builtin_type(element):
    """Returns the builtin type for ``type``. See also *get_builtin_value*."""
    value = element.get('type')
    if value is None:
        return None
    return get_builtin_value(value)


def is_builtin_type(element):
    """Checks whether ``element`` has a builtin type."""
    if get_builtin_type(element) is not None:
        return True
    return False


def is_complex_element(element):
    """Checks whether ``element`` is complex/is not builtin."""
    if is_builtin_type(element):
        return False
    elem_type = element.get('type')
    if elem_type is None:
        if element.find('{*}complexType') is not None:
            return True
        return False
    return True


def is_separate_element(element):
    """Checks whether the complex ``element`` has a separate complexType."""
    if (not is_complex_element(element) or
            element.find('{*}complexType') is not None):
        return False
    return True


def get_complex_type(element):
    """Returns the complexType of ``element``. Returns None if not complex."""
    if not is_complex_element(element):
        return None
    if is_separate_element(element):
        type_exp = "{{*}}complexType[@name=\"{}\"]".format(element.get('type'))
        return get_root(element).find(type_exp)
    return element.find('{*}complexType')


def is_builtin_attribute(attribute):
    """Checks whether ``attribute`` is builtin or has restrictions."""
    attr_type = attribute.get('type', '')
    return get_builtin_value(attr_type)


def is_separate_attribute(attribute):
    """Checks whether ``attribute`` has a separate simpleType."""
    if (attribute.find("{*}simpleType") is not None or
            is_builtin_attribute(attribute)):
        return False
    return True


def get_attribute_type(attribute):
    """Returns the simpleType of ``attribute``. Returns None if builtin."""
    attr_type = attribute.get('type')
    if is_separate_attribute(attribute):
        type_exp = "{{*}}simpleType[@name=\"{}\"]".format(attr_type)
        return get_root(attribute).find(type_exp)
    return attribute.find('{*}simpleType')


def get_attribute_base(base):
    """Returns the simpleType of ``base``."""
    type_exp = "{{*}}simpleType[@name=\"{}\"]".format(base.get('base'))
    return get_root(base).find(type_exp)


def get_order_from_group(group_ref):
    """Returns the order indicator from a group reference."""
    return get_order_elem(get_group_elem(group_ref))


def get_order_from_type(type_):
    """Returns the order indicator from a compleType."""
    if has_group_ref(type_):
        return get_order_from_group(get_group_ref(type_))
    return get_order_elem(type_)


def get_order_from_elem(element):
    """Returns the order indicator from an element."""
    type_ = get_complex_type(element)
    if type_ is not None:
        return get_order_from_type(type_)
    return None


def build_tag(root, tag):
    """Attaches the namespace from ``root`` to ``tag`` and returns it."""
    namespace = etree.QName(root).namespace
    if namespace is None:
        namespace = ''
    if namespace:
        namespace = '{' + namespace + '}'
    return namespace + tag


def make_schema_root(root, *elems):
    """
    Returns a xsd root.
    Namespaces are based on ``root`` and ``elems`` are added to the root.
    """
    root = etree.Element(build_tag(root, 'schema'), nsmap=root.nsmap)
    for elem in elems:
        root.append(elem)
        elem.attrib.pop('maxOccurs', None)
        elem.attrib.pop('minOccurs', None)
        elem.attrib.pop('ref', None)
    return root


def copy_schema(element, make_root=True, copy_level=0, rm_attr=False):
    """
    Copies the schema ``element`` and returns a tuple with all needed elements.

    ``make_root`` creates a proper xsd doc and returns it. See make_schema_root

    ``copy_level`` sets how many levels should be copied. *-1* is a full
    deepcopy, *0* a shallow copy, *1* copies the first level of child and
    so on.

    ``rm_attr`` removes all attributes from the final copy.
    """
    schema_elem = etree.Element(element.tag,
                                element.attrib,
                                element.nsmap)

    # a list to collect top level elements as we finish processing them
    results = [schema_elem]

    if is_complex_element(element):
        schema_type = deepcopy(get_complex_type(element))
        if is_separate_element(element):
            results.append(schema_type)
        else:
            schema_elem.append(schema_type)

        if get_order_from_elem(element) is not None:
            if has_group_ref(schema_type):
                group_elem = deepcopy(
                    get_group_elem(get_group_ref(get_complex_type(element))))
                order_elem = get_order_elem(group_elem)
                results.append(group_elem)
            else:
                order_elem = get_order_from_type(schema_type)
            if copy_level == 0:
                order_elem.clear()
                etree.SubElement(order_elem,
                                 build_tag(order_elem, 'any'),
                                 processContents='skip',
                                 minOccurs='0',
                                 maxOccurs='unbounded')
            else:
                for elem in get_order_from_elem(element).iter('{*}element'):
                    if (is_separate_element(elem) and
                            any(True for a in results
                                if a.get('name') == elem.get('type'))):
                        continue
                    for spec in copy_schema(elem, False, copy_level - 1)[1:]:
                        exists = any(True for a in results
                                     if a.get('name') == spec.get('name'))
                        if not exists:
                            results.append(spec)

        for attr in get_complex_type(element).iter('{*}attribute'):
            if rm_attr:
                attr.getparent().remove(attr)
                continue
            attr_t = attr.get('type')
            if attr_t is not None and not is_builtin_type(attr):
                type_exp = "{{*}}simpleType[@name=\"{}\"]".format(attr_t)
                attr_type_orig = get_root(element).find(type_exp)
                results.append(deepcopy(attr_type_orig))

    if make_root:
        return make_schema_root(schema_elem, *results)
    return tuple(results)
