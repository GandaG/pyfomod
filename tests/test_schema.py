from lxml import etree

import mock
from helpers import ElementTest, assert_elem_eq
from pyfomod import schema


def test_localname():
    test_func = schema.localname
    elem = etree.Element('{a}b')
    assert test_func(elem) == 'b'


def test_get_root():
    test_func = schema.get_root
    tree = etree.fromstring('<a><b><c><d/></c></b></a>')
    assert test_func(tree[0][0][0]) is tree


def test_get_min_occurs():
    test_func = schema.get_min_occurs

    elem = etree.fromstring("<a/>")
    assert test_func(elem) == 1

    elem = etree.fromstring("<a minOccurs='5'/>")
    assert test_func(elem) == 5


def test_get_max_occurs():
    test_func = schema.get_max_occurs

    elem = etree.fromstring("<a/>")
    assert test_func(elem) == 1

    elem = etree.fromstring("<a maxOccurs='5'/>")
    assert test_func(elem) == 5

    elem = etree.fromstring("<a maxOccurs='unbounded'/>")
    assert test_func(elem) is None


def test_get_doc_text():
    test_func = schema.get_doc_text

    text = "expected text"
    tree = etree.fromstring("<a>"
                            "<annotation>"
                            "<documentation>"
                            + text +
                            "</documentation>"
                            "</annotation>"
                            "</a>")
    assert test_func(tree) == text

    tree = etree.fromstring("<a/>")
    assert test_func(tree) is None


def test_get_order_elem():
    test_func = schema.get_order_elem

    tree = etree.Element('tree')
    order = etree.SubElement(tree, 'all')
    assert test_func(tree) is order

    tree = etree.Element('tree')
    order = etree.SubElement(tree, 'sequence')
    assert test_func(tree) is order

    tree = etree.Element('tree')
    order = etree.SubElement(tree, 'choice')
    assert test_func(tree) is order


def test_get_group_ref():
    test_func = schema.get_group_ref
    tree = etree.Element('complexType')
    group = etree.SubElement(tree, 'group', ref='a')
    assert_elem_eq(test_func(tree), group)


@mock.patch('pyfomod.schema.get_group_ref')
def test_has_group_ref(mock_get):
    test_func = schema.has_group_ref
    mock_get.return_value = None
    assert not test_func(mock.Mock(spec=ElementTest))
    mock_get.return_value = mock.Mock(spec=ElementTest)
    assert test_func(mock.Mock(spec=ElementTest))


def test_get_group_elem():
    test_func = schema.get_group_elem
    tree = etree.fromstring("<schema>"
                            "<element name='a'>"
                            "<group ref='group_ref'/>"
                            "</element>"
                            "<group name='group_ref'/>"
                            "</schema>")
    assert test_func(tree[0][0]) is tree[1]


def test_get_builtin_value():
    test_func = schema.get_builtin_value

    assert test_func('xs:string') == 'string'
    assert test_func('string') is None
    assert test_func('xs:boop') is None


def test_get_builtin_type():
    test_func = schema.get_builtin_type

    elem = etree.Element('a', type='xs:string')
    assert test_func(elem) == "string"

    elem = etree.Element('a', type='xs:a')
    assert test_func(elem) is None

    elem = etree.Element('a', type='string')
    assert test_func(elem) is None

    elem = etree.Element('a')
    assert test_func(elem) is None


def test_is_builtin_type():
    test_func = schema.is_builtin_type

    elem = etree.Element('a', type='xs:string')
    assert test_func(elem)

    elem = etree.Element('a', type='xs:a')
    assert not test_func(elem)

    elem = etree.Element('a', type='string')
    assert not test_func(elem)


def test_is_complex_element():
    test_func = schema.is_complex_element

    # simple element
    tree = etree.fromstring("<element name='a' "
                            "minOccurs='2' "
                            "maxOccurs='3'/>")
    assert not test_func(tree)

    # simple element
    tree = etree.fromstring("<element name='a' "
                            "type='xs:string'/>")
    assert not test_func(tree)

    # complex separate
    tree_elem = etree.fromstring("<element type='a'/>")
    tree_type = etree.fromstring("<complexType name='a'>"
                                 "<sequence/>"
                                 "</complexType>")
    tree = etree.Element('schema')
    tree.append(tree_elem)
    tree.append(tree_type)
    assert test_func(tree[0])

    # complex non separate
    tree = etree.fromstring("<element name='a'>"
                            "<complexType>"
                            "<sequence/>"
                            "</complexType>"
                            "</element>")
    assert test_func(tree)

    # complex grouped
    tree_elem = etree.fromstring("<element type='a'/>")
    tree_type = etree.fromstring("<complexType name='a'>"
                                 "<group ref='group_ref'/>"
                                 "</complexType>")
    tree_group = etree.fromstring("<group name='group_ref'>"
                                  "<all/>"
                                  "</group>")
    tree = etree.Element('schema')
    tree.append(tree_elem)
    tree.append(tree_type)
    tree.append(tree_group)
    assert test_func(tree[0])


def test_is_separate_element():
    test_func = schema.is_separate_element

    # simple element
    tree = etree.fromstring("<element name='a' "
                            "minOccurs='2' "
                            "maxOccurs='3'/>")
    assert not test_func(tree)

    # complex separate
    tree_elem = etree.fromstring("<element type='a'/>")
    tree_type = etree.fromstring("<complexType name='a'>"
                                 "<sequence/>"
                                 "</complexType>")
    tree = etree.Element('schema')
    tree.append(tree_elem)
    tree.append(tree_type)
    assert test_func(tree_elem)

    # complex non separate
    tree = etree.fromstring("<element name='a'>"
                            "<complexType>"
                            "<sequence/>"
                            "</complexType>"
                            "</element>")
    assert not test_func(tree)


def test_get_complex_type():
    test_func = schema.get_complex_type

    # simple element
    tree = etree.fromstring("<element name='a' "
                            "minOccurs='2' "
                            "maxOccurs='3'/>")
    assert test_func(tree) is None

    # complex separate
    tree_elem = etree.fromstring("<element type='a'/>")
    tree_type = etree.fromstring("<complexType name='a'>"
                                 "<sequence/>"
                                 "</complexType>")
    tree = etree.Element('schema')
    tree.append(tree_elem)
    tree.append(tree_type)
    assert test_func(tree_elem) is tree_type

    # complex non separate
    tree = etree.fromstring("<element name='a'>"
                            "<complexType>"
                            "<sequence/>"
                            "</complexType>"
                            "</element>")
    assert test_func(tree) is tree[0]


@mock.patch('pyfomod.schema.get_builtin_value')
def test_is_builtin_attribute(mock_value):
    test_func = schema.is_builtin_attribute

    test_func(etree.Element('a', **{'type': 'b'}))
    mock_value.assert_called_once_with('b')


@mock.patch('pyfomod.schema.is_builtin_attribute')
def test_is_separate_attribute(mock_builtin):
    test_func = schema.is_separate_attribute

    attr = etree.fromstring("<attribute>"
                            "<simpleType/>"
                            "</attribute>")
    mock_builtin.return_value = True
    assert not test_func(attr)

    attr = etree.Element('attribute')
    assert not test_func(attr)

    mock_builtin.return_value = False
    assert test_func(attr)


def test_get_attribute_type():
    test_func = schema.get_attribute_type

    tree = etree.fromstring("<schema>"
                            "<attribute name='a' type='b'/>"
                            "</schema>")
    assert test_func(tree[0]) is None

    tree = etree.fromstring("<schema>"
                            "<attribute name='a'>"
                            "<simpleType/>"
                            "</attribute>"
                            "</schema>")
    assert_elem_eq(test_func(tree[0]), tree[0][0])

    tree = etree.fromstring("<schema>"
                            "<attribute name='a' type='b'/>"
                            "<simpleType name='b'/>"
                            "</schema>")
    assert_elem_eq(test_func(tree[0]), tree[1])


def test_get_attribute_base():
    test_func = schema.get_attribute_base
    tree = etree.fromstring("<schema>"
                            "<restriction base='a'/>"
                            "<simpleType name='a'/>"
                            "</schema>")
    assert_elem_eq(test_func(tree[0]), tree[1])


def test_get_order_from_group():
    test_func = schema.get_order_from_group
    tree = etree.fromstring("<root>"
                            "<group ref='a'/>"  # doesnt matter where it is
                            "<group name='a'>"
                            "<all/>"
                            "</group>"
                            "</root>")
    assert_elem_eq(test_func(tree[0]), tree[1][0])


@mock.patch('pyfomod.schema.get_order_from_group')
@mock.patch('pyfomod.schema.get_order_elem')
def test_get_order_from_type(mock_order_elem, mock_order_group):
    test_func = schema.get_order_from_type

    tree = etree.fromstring("<complexType>"
                            "<group ref='a'/>"
                            "</complexType>")
    test_func(tree)
    mock_order_group.assert_called_once()

    tree = etree.fromstring("<complexType>"
                            "<sequence/>"
                            "</complexType>")
    test_func(tree)
    mock_order_elem.assert_called_once_with(tree)


@mock.patch('pyfomod.schema.get_order_from_type')
@mock.patch('pyfomod.schema.get_complex_type')
def test_get_order_from_elem(mock_type, mock_order):
    test_func = schema.get_order_from_elem
    assert test_func(None) is mock_order.return_value
    mock_type.assert_called_once_with(None)
    mock_order.assert_called_once_with(mock_type.return_value)

    mock_type.return_value = None
    assert test_func(None) is None


def test_build_tag():
    test_func = schema.build_tag
    elem = etree.Element('{a}root')
    assert test_func(elem, 'tag') == '{a}tag'


def test_make_schema_root():
    test_func = schema.make_schema_root
    elem = etree.Element('{a}root', nsmap={'xs': 'a'}, maxOccurs='1')
    expected = etree.fromstring("<xs:schema xmlns:xs='a'>"
                                "<xs:root/>"
                                "</xs:schema>")
    assert_elem_eq(test_func(elem, elem), expected)


@mock.patch('pyfomod.schema.make_schema_root')
def test_copy_schema(mock_root):
    test_func = schema.copy_schema

    # a simple element schema
    test_elem = etree.fromstring("<element name='a' "
                                 "type='xs:string' "
                                 "minOccurs='2' "
                                 "maxOccurs='3'/>")
    test_func(test_elem, True, -1)
    assert_elem_eq(mock_root.call_args[0][0], test_elem)
    assert_elem_eq(mock_root.call_args[0][1], test_elem)
    mock_root.reset_mock()
    assert_elem_eq(test_func(test_elem, False)[0], test_elem)

    # a complex element schema
    test_elem = etree.fromstring("<element name='aa' type='a'/>")
    test_type1 = etree.fromstring("<complexType name='a'>"
                                  "<sequence>"
                                  "<element name='child1' type='b'/>"
                                  "</sequence>"
                                  "<attribute name='attr1' type='attr1'/>"
                                  "</complexType>")
    test_type2 = etree.fromstring("<complexType name='b'>"
                                  "<sequence>"
                                  "<element name='child2'>"
                                  "<complexType>"
                                  "<sequence>"
                                  "<element name='child3' type='c'/>"
                                  "</sequence>"
                                  "<attribute name='attr2'>"
                                  "<simpleType>"
                                  "<restriction base='xs:integer'>"
                                  "<maxInclusive value='1000'/>"
                                  "</restriction>"
                                  "</simpleType>"
                                  "</attribute>"
                                  "</complexType>"
                                  "</element>"
                                  "</sequence>"
                                  "</complexType>")
    test_type3 = etree.fromstring("<complexType name='c'>"
                                  "<group ref='d'/>"
                                  "<attribute name='attr3' type='xs:string'/>"
                                  "</complexType>")
    test_group = etree.fromstring("<group name='d'>"
                                  "<sequence>"
                                  "<element name='child4' type='xs:string'/>"
                                  "</sequence>"
                                  "</group>")
    test_attr1 = etree.fromstring("<simpleType name='attr1'>"
                                  "<restriction base='xs:integer'>"
                                  "<maxInclusive value='1000'/>"
                                  "</restriction>"
                                  "</simpleType>")
    tree = etree.Element('schema')
    tree.append(test_elem)
    tree.append(test_type1)
    tree.append(test_type2)
    tree.append(test_type3)
    tree.append(test_group)
    tree.append(test_attr1)

    # full deep copy
    test_func(test_elem, True, -1)
    assert_elem_eq(mock_root.call_args[0][0], test_elem)
    assert_elem_eq(mock_root.call_args[0][1], test_elem)
    assert_elem_eq(mock_root.call_args[0][2], test_type1)
    assert_elem_eq(mock_root.call_args[0][3], test_type2)
    assert_elem_eq(mock_root.call_args[0][4], test_type3)
    assert_elem_eq(mock_root.call_args[0][5], test_group)
    assert_elem_eq(mock_root.call_args[0][6], test_attr1)
    mock_root.reset_mock()
    assert_elem_eq(test_func(test_elem, False, -1)[0], test_elem)
    assert_elem_eq(test_func(test_elem, False, -1)[1], test_type1)
    assert_elem_eq(test_func(test_elem, False, -1)[2], test_type2)
    assert_elem_eq(test_func(test_elem, False, -1)[3], test_type3)
    assert_elem_eq(test_func(test_elem, False, -1)[4], test_group)
    assert_elem_eq(test_func(test_elem, False, -1)[5], test_attr1)

    # full deep copy by specifying copy level
    test_func(test_elem, True, 4)
    assert_elem_eq(mock_root.call_args[0][0], test_elem)
    assert_elem_eq(mock_root.call_args[0][1], test_elem)
    assert_elem_eq(mock_root.call_args[0][2], test_type1)
    assert_elem_eq(mock_root.call_args[0][3], test_type2)
    assert_elem_eq(mock_root.call_args[0][4], test_type3)
    assert_elem_eq(mock_root.call_args[0][5], test_group)
    assert_elem_eq(mock_root.call_args[0][6], test_attr1)
    mock_root.reset_mock()
    assert_elem_eq(test_func(test_elem, False, 4)[0], test_elem)
    assert_elem_eq(test_func(test_elem, False, 4)[1], test_type1)
    assert_elem_eq(test_func(test_elem, False, 4)[2], test_type2)
    assert_elem_eq(test_func(test_elem, False, 4)[3], test_type3)
    assert_elem_eq(test_func(test_elem, False, 4)[4], test_group)
    assert_elem_eq(test_func(test_elem, False, -1)[5], test_attr1)

    # level 1 copy
    expt_type2 = etree.fromstring("<complexType name='b'>"
                                  "<sequence>"
                                  "<any processContents='skip' "
                                  "minOccurs='0' maxOccurs='unbounded'/>"
                                  "</sequence>"
                                  "</complexType>")
    test_func(test_elem, True, 1)
    assert_elem_eq(mock_root.call_args[0][0], test_elem)
    assert_elem_eq(mock_root.call_args[0][1], test_elem)
    assert_elem_eq(mock_root.call_args[0][2], test_type1)
    assert_elem_eq(mock_root.call_args[0][3], expt_type2)
    assert_elem_eq(mock_root.call_args[0][4], test_attr1)
    mock_root.reset_mock()
    assert_elem_eq(test_func(test_elem, False, 1)[0], test_elem)
    assert_elem_eq(test_func(test_elem, False, 1)[1], test_type1)
    assert_elem_eq(test_func(test_elem, False, 1)[2], expt_type2)
    assert_elem_eq(test_func(test_elem, False, 1)[3], test_attr1)

    # level 0 copy
    expt_type1 = etree.fromstring("<complexType name='a'>"
                                  "<sequence>"
                                  "<any processContents='skip' "
                                  "minOccurs='0' maxOccurs='unbounded'/>"
                                  "</sequence>"
                                  "<attribute name='attr1' type='attr1'/>"
                                  "</complexType>")
    expt_attr = etree.fromstring("<complexType name='a'>"
                                 "<sequence>"
                                 "<any processContents='skip' "
                                 "minOccurs='0' maxOccurs='unbounded'/>"
                                 "</sequence>"
                                 "</complexType>")
    test_func(test_elem, True, 0)
    assert_elem_eq(mock_root.call_args[0][0], test_elem)
    assert_elem_eq(mock_root.call_args[0][1], test_elem)
    assert_elem_eq(mock_root.call_args[0][2], expt_type1)
    assert_elem_eq(mock_root.call_args[0][3], test_attr1)
    mock_root.reset_mock()
    assert_elem_eq(test_func(test_elem, False, 0)[0], test_elem)
    assert_elem_eq(test_func(test_elem, False, 0)[1], expt_type1)
    assert_elem_eq(test_func(test_elem, False, 0)[2], test_attr1)
    mock_root.reset_mock()
    assert_elem_eq(test_func(test_elem, False, 0, True)[0], test_elem)
    assert_elem_eq(test_func(test_elem, False, 0, True)[1], expt_attr)
