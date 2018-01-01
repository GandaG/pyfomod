from lxml import etree
from pyfomod import tree, validation

import mock
import pytest
from helpers import ElementTest, assert_elem_eq, make_element, test_parser


def test_copy_element():
    test_func = tree.copy_element

    elem_orig = etree.fromstring('<elem a="1">text</elem>')
    assert_elem_eq(test_func(elem_orig), elem_orig)

    elem_orig = etree.fromstring('<elem a="1">text<child/>tail</elem>')
    assert_elem_eq(test_func(elem_orig, -1), elem_orig)


class Test_FomodElement:
    def test_max_occurences(self):
        test_func = tree.FomodElement.max_occurences.fget
        elem = ElementTest()
        elem._schema_element = etree.Element('element', maxOccurs='5')
        assert test_func(elem) == 5

    def test_min_occurences(self):
        test_func = tree.FomodElement.min_occurences.fget
        elem = ElementTest()
        elem._schema_element = etree.Element('element', minOccurs='5')
        assert test_func(elem) == 5

    def test_type(self):
        test_func = tree.FomodElement.type.fget

        elem = ElementTest()
        elem._schema_element = etree.fromstring("<element name='a'>"
                                                "<complexType>"
                                                "<all/>"
                                                "</complexType>"
                                                "</element>")
        assert test_func(elem) is None

        elem._schema_element = etree.fromstring("<element name='a' "
                                                "type='a:string'/>")
        assert test_func(elem) == 'string'

        elem._schema_element = etree.fromstring("<element name='a'>"
                                                "<complexType>"
                                                "<simpleContent>"
                                                "<extension base='a:string'/>"
                                                "</simpleContent>"
                                                "</complexType>"
                                                "</element>")
        assert test_func(elem) == 'string'

    def test_comment(self):
        test_func = tree.FomodElement.comment.fget
        elem = ElementTest()
        elem._comment = None
        assert test_func(elem) == ""

        elem._comment = etree.Comment('comment')
        assert test_func(elem) == "comment"

        test_func = tree.FomodElement.comment.fset

        parent = ElementTest()
        parent.append(elem)
        elem._comment = None
        test_func(elem, None)
        assert elem._comment is None

        elem._comment = etree.Comment('comment')
        parent.insert(0, elem._comment)
        test_func(elem, None)
        assert elem._comment is None

        elem._comment = None
        test_func(elem, "comment")
        assert elem._comment.text == "comment"

        elem._comment = etree.Comment('comment')
        test_func(elem, "test")
        assert elem._comment.text == "test"

    def test_doc(self):
        test_func = tree.FomodElement.doc.fget

        elem = ElementTest()
        elem._schema_element = etree.fromstring("<element name='a'>"
                                                "<annotation>"
                                                "<documentation>"
                                                "doc text"
                                                "</documentation>"
                                                "</annotation>"
                                                "</element>")
        assert test_func(elem) == 'doc text'

        elem._schema_element = etree.Element('element', name='a')
        assert test_func(elem) == ''

    def test_valid_children_parse_order(self):
        test_func = tree.FomodElement._valid_children_parse_order
        schema = etree.fromstring("<root>"
                                  "<sequence maxOccurs='3'>"
                                  "<element name='a' type='xs:decimal'/>"
                                  "<choice minOccurs='0'>"
                                  "<group ref='b'/>"
                                  "</choice>"
                                  "<any minOccurs='2' maxOccurs='10'/>"
                                  "</sequence>"
                                  "<group name='b'>"
                                  "<all>"
                                  "<element name='c' type='xs:string'/>"
                                  "</all>"
                                  "</group>"
                                  "</root>")
        all_ord = tree.OrderIndicator('all',
                                      [tree.ChildElement('c', 1, 1)],
                                      1, 1)
        choice_ord = tree.OrderIndicator('choice', [all_ord], 1, 0)
        expected = tree.OrderIndicator('sequence',
                                       [tree.ChildElement('a', 1, 1),
                                        choice_ord,
                                        tree.ChildElement(None, 10, 2)],
                                       3, 1)
        assert test_func(schema[0]) == expected

    def test_find_valid_attribute(self):
        test_func = tree.FomodElement._find_valid_attribute

        elem = ElementTest()
        attr = tree.Attribute('MachineVersion', None, None,
                              'string', 'optional', None)
        elem.valid_attributes = lambda: [attr]
        assert test_func(elem, 'MachineVersion') == attr

        elem.valid_attributes = lambda: []
        with pytest.raises(ValueError):
            test_func(elem, 'MachineVersion')

    def test_required_children_choice(self):
        test_func = tree.FomodElement._required_children_choice

        elem = ElementTest()
        test_choice = tree.OrderIndicator('choice', [], 2, 2)
        assert test_func(elem, test_choice) == []

        test_child = tree.ChildElement('child', 2, 2)
        test_choice = tree.OrderIndicator('choice', [test_child], 2, 2)
        assert test_func(elem, test_choice) == [('child', 4)]

        test_choice2 = mock.Mock(spec=tree.OrderIndicator)
        test_choice2.type = 'choice'
        test_choice = tree.OrderIndicator('choice', [test_choice2], 2, 2)
        elem._required_children_choice = lambda _: [('child', 2)]
        assert test_func(elem, test_choice) == [('child', 4)]

        test_sequence = mock.Mock(spec=tree.OrderIndicator)
        test_sequence.type = 'sequence'
        test_choice = tree.OrderIndicator('choice', [test_sequence], 2, 2)
        elem._required_children_sequence = lambda _: [('child', 2)]
        assert test_func(elem, test_choice) == [('child', 4)]

    def test_required_children_sequence(self):
        test_func = tree.FomodElement._required_children_sequence

        elem = ElementTest()
        test_sequence = tree.OrderIndicator('sequence', [], 2, 2)
        assert test_func(elem, test_sequence) == []

        test_child = mock.Mock(spec=tree.ChildElement)
        test_child.tag = 'child'
        test_child.min_occ = 5
        test_sequence = tree.OrderIndicator('sequence', [test_child], 2, 2)
        assert test_func(elem, test_sequence) == [('child', 10)]

        test_choice = mock.Mock(spec=tree.OrderIndicator)
        test_choice.type = 'choice'
        test_sequence = tree.OrderIndicator('sequence', [test_choice], 2, 2)
        elem._required_children_choice = lambda _: [('child', 2)]
        assert test_func(elem, test_sequence) == [('child', 4)]

        test_sequence = mock.Mock(spec=tree.OrderIndicator)
        test_sequence.type = 'sequence'
        test_sequence = tree.OrderIndicator('sequence', [test_sequence],
                                            2, 2)
        elem._required_children_sequence = lambda _: [('child', 2)]
        assert test_func(elem, test_sequence) == [('child', 4)]

    @mock.patch('pyfomod.tree.copy_element')
    @mock.patch('pyfomod.tree.copy_schema')
    def test_find_possible_index(self, mock_schema, mock_copy):
        test_func = tree.FomodElement._find_possible_index

        # not valid
        test_tag = 'test'
        schema = etree.fromstring("<schema "
                                  "xmlns='http://www.w3.org/2001/XMLSchema'>"
                                  "<element name='elem'>"
                                  "<complexType/>"
                                  "</element>"
                                  "</schema>")
        elem = etree.Element('elem')
        mock_self = mock.MagicMock(spec=tree.FomodElement)
        mock_self._schema_element = mock.Mock(spec=ElementTest)
        mock_copy.return_value = elem
        mock_schema.return_value = schema
        assert test_func(mock_self, test_tag) is None

        # valid in last
        schema = etree.fromstring("<schema "
                                  "xmlns='http://www.w3.org/2001/XMLSchema'>"
                                  "<element name='elem'>"
                                  "<complexType>"
                                  "<sequence>"
                                  "<element name='test' minOccurs='0'>"
                                  "<complexType/>"
                                  "</element>"
                                  "</sequence>"
                                  "</complexType>"
                                  "</element>"
                                  "</schema>")
        elem = etree.Element('elem')
        mock_copy.return_value = elem
        mock_schema.return_value = schema
        assert test_func(mock_self, test_tag) == -1

        # valid in index 1
        schema = etree.fromstring("<schema "
                                  "xmlns='http://www.w3.org/2001/XMLSchema'>"
                                  "<element name='elem'>"
                                  "<complexType>"
                                  "<sequence>"
                                  "<element name='child1'/>"
                                  "<element name='child2' minOccurs='0'/>"
                                  "<element name='child3'/>"
                                  "</sequence>"
                                  "</complexType>"
                                  "</element>"
                                  "</schema>")
        elem = etree.Element('elem')
        etree.SubElement(elem, 'child1')
        etree.SubElement(elem, 'child3')
        test_tag = 'child2'
        mock_copy.return_value = elem
        mock_schema.return_value = schema
        assert test_func(mock_self, test_tag) == 1

    @mock.patch('lxml.etree.SubElement')
    def test_setup_new_element(self, mock_subelem):
        test_func = tree.FomodElement._setup_new_element

        elem = ElementTest()
        elem.set_attribute = elem.set

        mock_subelem.side_effect = lambda x, y: mock.Mock() \
            if x.append(etree.Element(y)) is None else mock.Mock()

        attr_rest = tree.AttrRestriction('enumeration',
                                         [tree.AttrRestElement('enum',
                                                               None)],
                                         *[None] * 10)
        req_attr = [tree.Attribute('attr_default',
                                   None,
                                   'default',
                                   None,
                                   'required',
                                   None),
                    tree.Attribute('attr_rest',
                                   None,
                                   None,
                                   None,
                                   'required',
                                   attr_rest),
                    tree.Attribute('attr_none',
                                   None,
                                   None,
                                   None,
                                   'required',
                                   None)]
        elem.required_attributes = lambda: req_attr
        elem.required_children = lambda: [('child1', 1),
                                          ('child2', 7),
                                          ('child3', 2)]
        test_func(elem)
        assert elem.get('attr_default') == 'default'
        assert elem.get('attr_rest') == 'enum'
        assert elem.get('attr_none') == ''
        assert len(elem.findall('child1')) == 1
        assert len(elem.findall('child2')) == 7
        assert len(elem.findall('child3')) == 2

    def test_lookup_element(self):
        test_func = tree.FomodElement._lookup_element

        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a'>"
                                  "<xs:complexType>"
                                  "<xs:all>"
                                  "<xs:element name='b' type='bt'/>"
                                  "</xs:all>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "<xs:complexType name='bt'>"
                                  "<xs:choice>"
                                  "<xs:element name='c' type='ct'/>"
                                  "</xs:choice>"
                                  "</xs:complexType>"
                                  "<xs:complexType name='ct'>"
                                  "<xs:group ref='cg'/>"
                                  "</xs:complexType>"
                                  "<xs:group name='cg'>"
                                  "<xs:sequence>"
                                  "<xs:element name='d' type='xs:string'/>"
                                  "</xs:sequence>"
                                  "</xs:group>"
                                  "</xs:schema>")
        elem_a = make_element('a')
        elem_a._schema = schema
        elem_b = make_element('b')
        elem_b._schema = schema
        elem_a.append(elem_b)
        elem_c = make_element('c')
        elem_c._schema = schema
        elem_b.append(elem_c)
        elem_d = make_element('d')
        elem_d._schema = schema
        elem_c.append(elem_d)

        assert_elem_eq(test_func(elem_a), schema[0])
        assert_elem_eq(test_func(elem_b), schema[0][0][0][0])
        assert_elem_eq(test_func(elem_c), schema[1][0][0])
        assert_elem_eq(test_func(elem_d), schema[3][0][0])

    def test_assert_valid(self):
        test_func = tree.FomodElement._assert_valid

        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a' type='xs:integer'/>"
                                  "</xs:schema>")
        elem = make_element('a', 'text')
        elem._schema_element = schema[0]
        with pytest.raises(RuntimeError) as exc_info:
            test_func(elem)

        assert str(exc_info.value) == ("This element is invalid with the "
                                       "following message: Element 'a': 'text'"
                                       " is not a valid value of the atomic "
                                       "type 'xs:integer'.\nCorrect this "
                                       "before using this API.")

    def test_init(self):
        test_func = tree.FomodElement._init

        elem = ElementTest()
        elem._lookup_element = lambda: None
        elem_c = etree.Comment('elem')
        elem.addprevious(elem_c)

        test_func(elem)
        assert elem._comment is elem_c
        assert elem._schema_element is None
        assert elem._schema is validation.FOMOD_SCHEMA_TREE

    def test_valid_attributes(self):
        test_func = tree.FomodElement.valid_attributes

        elem = ElementTest()
        elem._assert_valid = lambda: None

        # simple element - no attributes
        schema = etree.fromstring("<element name='a' type='xs:string'/>")
        elem._schema_element = schema
        assert test_func(elem) == []

        # a simple string attribute
        schema = etree.fromstring("<element name='a'>"
                                  "<complexType>"
                                  "<attribute name='attr' type='xs:string'/>"
                                  "</complexType>"
                                  "</element>")
        expected = tree.Attribute("attr", None, None,
                                  "string", "optional", None)
        elem._schema_element = schema
        assert test_func(elem) == [expected]

        # same as above vis attributeGroup
        schema = etree.fromstring("<schema>"
                                  "<element name='a'>"
                                  "<complexType>"
                                  "<attributeGroup ref='attrgr'/>"
                                  "</complexType>"
                                  "</element>"
                                  "<attributeGroup name='attrgr'>"
                                  "<attribute name='attr' type='xs:string'/>"
                                  "</attributeGroup>"
                                  "</schema>")
        expected = tree.Attribute("attr", None, None,
                                  "string", "optional", None)
        elem._schema_element = schema[0]
        assert test_func(elem) == [expected]

        # restrictions
        schema = etree.fromstring("<element name='a'>"
                                  "<complexType>"
                                  "<attribute name='attr'>"
                                  "<annotation>"
                                  "<documentation>"
                                  "Attribute documentation."
                                  "</documentation>"
                                  "</annotation>"
                                  "<simpleType>"
                                  "<restriction base='xs:string'>"
                                  "<enumeration value='aa'>"
                                  "<annotation>"
                                  "<documentation>"
                                  "Enumeration documentation."
                                  "</documentation>"
                                  "</annotation>"
                                  "</enumeration>"
                                  "<enumeration value='bb'/>"
                                  "</restriction>"
                                  "</simpleType>"
                                  "</attribute>"
                                  "<attribute name='child'>"
                                  "<simpleType>"
                                  "<restriction base='other_attr'/>"
                                  "</simpleType>"
                                  "</attribute>"
                                  "</complexType>"
                                  "</element>")
        rest_list = [tree.AttrRestElement('aa',
                                          "Enumeration documentation."),
                     tree.AttrRestElement('bb', None)]
        attr_rest = tree.AttrRestriction('enumeration ', rest_list,
                                         None, None, None, None, None,
                                         None, None, None, None, None)
        child_rest = tree.AttrRestriction('', [],
                                          None, None, None, None, None,
                                          None, None, None, None, None)
        expected = [tree.Attribute('attr', "Attribute documentation.",
                                   None, 'string', 'optional', attr_rest),
                    tree.Attribute('child', None, None, 'other_attr',
                                   'optional', child_rest)]
        elem._schema_element = schema
        assert test_func(elem) == expected

    def test_required_attributes(self):
        test_func = tree.FomodElement.required_attributes

        attr1 = tree.Attribute("attr1", None, None,
                               "string", "optional", None)
        attr2 = tree.Attribute("attr2", None, None,
                               "string", "required", None)
        attr3 = tree.Attribute("attr3", None, None,
                               "string", "optional", None)
        attr4 = tree.Attribute("attr4", None, None,
                               "string", "required", None)

        elem = ElementTest()
        elem.valid_attributes = lambda: [attr1, attr2, attr3, attr4]
        assert test_func(elem) == [attr2, attr4]

    def test_get_attribute(self):
        test_func = tree.FomodElement.get_attribute

        attr1 = tree.Attribute("attr1", None, None,
                               "string", "optional", None)
        attr2 = tree.Attribute("attr2", None, "default",
                               "string", "required", None)

        elem = ElementTest()
        elem._assert_valid = lambda: None
        elem._find_valid_attribute = lambda x: attr1 if x == 'attr1' else attr2
        elem.set('attr3', 'existing')

        assert test_func(elem, 'attr1') == ''
        assert test_func(elem, 'attr2') == 'default'
        assert test_func(elem, 'attr3') == 'existing'

    def test_set_attribute(self):
        test_func = tree.FomodElement.set_attribute
        ElementTest._find_valid_attribute = \
            tree.FomodElement._find_valid_attribute
        ElementTest.valid_attributes = tree.FomodElement.valid_attributes
        ElementTest._assert_valid = tree.FomodElement._assert_valid

        # normal
        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a'>"
                                  "<xs:complexType>"
                                  "<xs:attribute name='b' type='xs:integer'/>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "</xs:schema>")
        elem = make_element('a')
        elem._schema_element = schema[0]
        test_func(elem, 'b', 1)
        assert elem.get('b') == '1'

        # wrong type
        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a'>"
                                  "<xs:complexType>"
                                  "<xs:attribute name='b' type='xs:integer'/>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "</xs:schema>")
        elem = make_element('a')
        elem._schema_element = schema[0]
        with pytest.raises(ValueError):
            test_func(elem, 'b', 'boop')
        assert elem.get('b') is None

        # restriction
        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a'>"
                                  "<xs:complexType>"
                                  "<xs:attribute name='b'>"
                                  "<xs:simpleType>"
                                  "<xs:restriction base='xs:string'>"
                                  "<xs:enumeration value='doop'/>"
                                  "</xs:restriction>"
                                  "</xs:simpleType>"
                                  "</xs:attribute>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "</xs:schema>")
        elem = make_element('a')
        elem._schema_element = schema[0]
        with pytest.raises(ValueError):
            test_func(elem, 'b', 'boop')
        assert elem.get('b') is None

        # removal
        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a'>"
                                  "<xs:complexType>"
                                  "<xs:attribute name='b' type='xs:integer' "
                                  "use='optional'/>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "</xs:schema>")
        elem = make_element('a')
        elem._schema_element = schema[0]
        elem.set('b', '1')
        test_func(elem, 'b', None)
        assert elem.get('b') is None

        # removal non existing
        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a'>"
                                  "<xs:complexType>"
                                  "<xs:attribute name='b' type='xs:integer' "
                                  "use='optional'/>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "</xs:schema>")
        elem = make_element('a')
        elem._schema_element = schema[0]
        with pytest.raises(ValueError):
            test_func(elem, 'b', None)

        # removal required
        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a'>"
                                  "<xs:complexType>"
                                  "<xs:attribute name='b' type='xs:integer' "
                                  "use='required'/>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "</xs:schema>")
        elem = make_element('a')
        elem._schema_element = schema[0]
        elem.set('b', '1')
        with pytest.raises(ValueError):
            test_func(elem, 'b', None)

    def test_children(self):
        test_func = tree.FomodElement.children

        root = ElementTest()
        elem1 = etree.SubElement(root, 'a')
        elem2 = etree.SubElement(root, 'b')
        elem3 = etree.SubElement(root, 'c')

        assert test_func(root) == [elem1, elem2, elem3]

    def test_valid_children(self):
        test_func = tree.FomodElement.valid_children

        elem = ElementTest()
        elem._assert_valid = lambda: None

        elem._schema_element = etree.fromstring("<element name='a' "
                                                "type='xs:string'/>")
        assert test_func(elem) is None

        elem._schema_element = etree.fromstring("<element name='a'>"
                                                "<complexType>"
                                                "<all/>"
                                                "</complexType>"
                                                "</element>")
        elem._valid_children_parse_order = lambda x: 'success' \
            if assert_elem_eq(x, elem._schema_element[0][0]) is None \
            else 'failure'
        assert test_func(elem) == 'success'

    def test_required_children(self):
        test_func = tree.FomodElement.required_children

        elem = ElementTest()
        elem.valid_children = lambda: None
        assert test_func(elem) == []

        test_choice = mock.Mock(spec=tree.OrderIndicator)
        test_choice.type = 'choice'
        elem.valid_children = lambda: test_choice
        elem._required_children_choice = lambda x: [('child', 2)] \
            if x is test_choice else 'failure'
        assert test_func(elem) == [('child', 2)]

        test_sequence = mock.Mock(spec=tree.OrderIndicator)
        test_sequence.type = 'sequence'
        elem.valid_children = lambda: test_sequence
        elem._required_children_sequence = lambda x: [('child', 2)] \
            if x is test_sequence else 'failure'
        assert test_func(elem) == [('child', 2)]

    def test_can_add_child(self):
        test_func = tree.FomodElement.can_add_child

        elem = ElementTest()
        elem._assert_valid = lambda: None

        with pytest.raises(TypeError):
            # the second arg is any type other than string or FomodElement
            test_func(elem, 0)

        elem._find_possible_index = lambda _: None
        assert not test_func(elem, 'tag')
        elem._find_possible_index = lambda _: 'success'
        assert test_func(elem, 'tag')

        elem._find_possible_index = lambda _: None
        mock_parent = mock.Mock(spec=tree.FomodElement)
        mock_child = mock.Mock(spec=tree.FomodElement)
        mock_child.getparent.return_value = mock_parent
        mock_parent.can_remove_child.return_value = False
        assert not test_func(elem, mock_child)
        elem._find_possible_index = lambda _: 'success'
        assert not test_func(elem, mock_child)

        elem._find_possible_index = lambda _: None
        mock_child.getparent.return_value = None
        assert not test_func(elem, mock_child)
        elem._find_possible_index = lambda _: 'success'
        assert test_func(elem, mock_child)

    def test_add_child(self):
        test_func = tree.FomodElement.add_child

        elem = ElementTest()
        elem._assert_valid = lambda: None

        with pytest.raises(TypeError):
            test_func(elem, 0)

        elem._find_possible_index = lambda _: None
        mock_child = mock.Mock(spec=tree.FomodElement)
        mock_child.tag = 'a'
        with pytest.raises(ValueError):
            test_func(elem, mock_child)

        with mock.patch('lxml.etree.SubElement') as subelem_patch:
            elem_newchild = ElementTest()
            elem_newchildcomment = etree.Comment('comment')

            subelem_patch.side_effect = lambda x, y: elem_newchild \
                if x.append(elem_newchild) is None else 'failure'
            elem._find_possible_index = lambda _: 0
            elem_newchild._setup_new_element = lambda: None
            elem_newchild._comment = elem_newchildcomment

            test_func(elem, 'tag')
            assert list(elem) == [elem_newchildcomment, elem_newchild]

        with mock.patch('pyfomod.tree.isinstance') as inst_patch:
            elem = ElementTest()
            elem._assert_valid = lambda: None
            elem._find_possible_index = lambda _: 0

            inst_patch.side_effect = lambda _, y: y is tree.FomodElement
            elem_child = ElementTest()
            elem_child._comment = None

            test_func(elem, elem_child)
            assert list(elem) == [elem_child]

            elem_parent = ElementTest()
            elem_parent.append(elem_child)
            elem_parent.remove_child = elem_parent.remove

            test_func(elem, elem_child)
            assert list(elem_parent) == []
            assert list(elem) == [elem_child]

    @mock.patch('pyfomod.tree.copy_element')
    @mock.patch('pyfomod.tree.copy_schema')
    def test_can_remove_child(self, mock_schema, mock_copy):
        test_func = tree.FomodElement.can_remove_child

        # errors
        with pytest.raises(TypeError):
            # second arg is anything but FomodElement
            mock_self = mock.Mock(spec=tree.FomodElement)
            test_func(mock_self, 0)
        mock_self = mock.MagicMock(spec=tree.FomodElement)
        mock_self.__iter__.return_value = []
        mock_child = mock.MagicMock(spec=tree.FomodElement)
        with pytest.raises(ValueError):
            test_func(mock_self, mock_child)

        # normal
        schema = etree.fromstring("<xs:schema xmlns:xs='http://www."
                                  "w3.org/2001/XMLSchema'>"
                                  "<xs:element name='elem'>"
                                  "<xs:complexType>"
                                  "<xs:sequence>"
                                  "<xs:element name='child1' type='empty'/>"
                                  "<xs:element name='child2' type='empty'/>"
                                  "</xs:sequence>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "<xs:complexType name='empty'/>"
                                  "</xs:schema>")
        elem = etree.Element('elem')
        etree.SubElement(elem, 'child1')
        etree.SubElement(elem, 'child2')
        mock_child = mock.MagicMock(spec=tree.FomodElement)
        mock_self.__contains__ = lambda y, x: True if x is mock_child \
            else False
        mock_self._schema_element = mock.Mock(spec=ElementTest)
        mock_copy.return_value = elem
        mock_schema.return_value = schema
        mock_self.index.return_value = 1
        assert not test_func(mock_self, mock_child)

    def test_remove_child(self):
        test_func = tree.FomodElement.remove_child

        elem = ElementTest()
        elem._assert_valid = lambda: None
        elem_child = ElementTest()
        elem_child._comment = None

        elem.can_remove_child = lambda _: False
        with pytest.raises(ValueError):
            test_func(elem, 0)

        elem.can_remove_child = lambda _: True
        elem.append(elem_child)
        test_func(elem, elem_child)
        assert len(elem) == 0

        elem_child._comment = etree.Comment('comment')
        elem.append(elem_child._comment)
        elem.append(elem_child)
        test_func(elem, elem_child)
        assert len(elem) == 0

    @mock.patch('pyfomod.tree.copy_element')
    @mock.patch('pyfomod.tree.copy_schema')
    def test_can_replace_child(self, mock_schema, mock_copy):
        test_func = tree.FomodElement.can_replace_child

        # errors
        with pytest.raises(TypeError):
            # second arg is anything but FomodElement
            mock_self = mock.Mock(spec=tree.FomodElement)
            test_func(mock_self, 0, 0)
        mock_self = mock.MagicMock(spec=tree.FomodElement)
        mock_old = mock.MagicMock(spec=tree.FomodElement)
        mock_new = mock.MagicMock(spec=tree.FomodElement)
        with pytest.raises(ValueError):
            test_func(mock_self, mock_old, mock_new)

        # normal
        schema = etree.fromstring("<xs:schema xmlns:xs='http://www."
                                  "w3.org/2001/XMLSchema'>"
                                  "<xs:element name='elem'>"
                                  "<xs:complexType>"
                                  "<xs:choice>"
                                  "<xs:element name='child1' type='empty'/>"
                                  "<xs:element name='child2' type='empty'/>"
                                  "</xs:choice>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "<xs:complexType name='empty'/>"
                                  "</xs:schema>")
        elem = etree.Element('elem')
        etree.SubElement(elem, 'child1')
        mock_old = mock.MagicMock(spec=tree.FomodElement)
        mock_old.tag = 'child1'
        mock_new = mock.MagicMock(spec=tree.FomodElement)
        mock_new.tag = 'child2'
        mock_self = mock.MagicMock(spec=tree.FomodElement)
        mock_self.__contains__ = lambda y, x: True \
            if x is mock_old else False
        mock_self._schema_element = mock.Mock(spec=ElementTest)
        mock_copy.return_value = elem
        mock_schema.return_value = schema
        mock_self.index.return_value = 0
        mock_new.getparent.return_value = None
        assert test_func(mock_self, mock_old, mock_new)
        mock_parent = mock.Mock(spec=tree.FomodElement)
        mock_new.getparent.return_value = mock_parent
        mock_parent.can_remove_child = lambda x: False \
            if x is mock_new else True
        assert not test_func(mock_self, mock_old, mock_new)

    def test_replace_child(self):
        test_func = tree.FomodElement.replace_child

        elem = ElementTest()
        elem._assert_valid = lambda: None

        elem.can_replace_child = lambda x, y: False
        with pytest.raises(ValueError):
            test_func(elem, 0, 0)

        elem.can_replace_child = lambda x, y: True

        elem_oldchild = ElementTest()
        elem_oldchild._comment = None
        elem_newchild = ElementTest()
        elem_newchild._comment = None
        parent = ElementTest()
        parent.remove_child = parent.remove

        elem.append(elem_oldchild)
        test_func(elem, elem_oldchild, elem_newchild)
        assert list(elem) == [elem_newchild]

        com_new = elem_newchild._comment = etree.Comment('new')
        com_old = elem_oldchild._comment = etree.Comment('old')
        parent.append(com_new)
        parent.append(elem_newchild)
        elem.append(com_old)
        elem.append(elem_oldchild)
        test_func(elem, elem_oldchild, elem_newchild)
        assert list(elem) == [com_new, elem_newchild]

    def test_can_reorder_child(self):
        test_func = tree.FomodElement.can_reorder_child
        ElementTest._assert_valid = tree.FomodElement._assert_valid

        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a'>"
                                  "<xs:complexType>"
                                  "<xs:sequence>"
                                  "<xs:element name='b' "
                                  "maxOccurs='5' minOccurs='0'/>"
                                  "</xs:sequence>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "</xs:schema>")
        root = make_element('a')
        root._schema_element = schema[0]
        elem1 = make_element('b')
        elem1._schema_element = schema[0][0][0][0]

        with pytest.raises(ValueError):
            test_func(root, elem1, 0)

        root.append(elem1)
        assert not test_func(root, elem1, 0)

        elem2 = make_element('b')
        elem2._schema_element = schema[0][0][0][0]
        root.append(elem2)
        assert not test_func(root, elem1, 2)
        assert not test_func(root, elem1, -2)

        elem3 = make_element('b')
        elem3._schema_element = schema[0][0][0][0]
        root.append(elem3)
        assert test_func(root, elem1, 2)
        assert test_func(root, elem1, 0)
        assert test_func(root, elem2, 1)
        assert test_func(root, elem2, -1)
        assert test_func(root, elem3, 0)
        assert test_func(root, elem3, -2)

    def test_reorder_child(self):
        test_func = tree.FomodElement.reorder_child
        ElementTest._assert_valid = tree.FomodElement._assert_valid
        ElementTest.can_reorder_child = tree.FomodElement.can_reorder_child
        ElementTest._comment = None

        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a'>"
                                  "<xs:complexType>"
                                  "<xs:sequence>"
                                  "<xs:element name='b' "
                                  "maxOccurs='5' minOccurs='0'/>"
                                  "</xs:sequence>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "</xs:schema>")
        root = make_element('a')
        root._schema_element = schema[0]
        elem1 = make_element('b')
        elem1._schema_element = schema[0][0][0][0]

        with pytest.raises(ValueError):
            test_func(root, elem1, 0)

        root.append(elem1)
        with pytest.raises(ValueError):
            test_func(root, elem1, 0)

        elem2 = make_element('b')
        elem2._schema_element = schema[0][0][0][0]
        root.append(elem2)
        with pytest.raises(ValueError):
            test_func(root, elem1, 2)
        with pytest.raises(ValueError):
            test_func(root, elem1, -2)

        elem3 = make_element('b')
        elem3._schema_element = schema[0][0][0][0]
        root.append(elem3)
        test_func(root, elem2, 1)
        assert list(root) == [elem1, elem3, elem2]
        test_func(root, elem2, -1)
        assert list(root) == [elem1, elem2, elem3]

        elem2._comment = etree.Comment('comment elem2')
        root.insert(root.index(elem2), elem2._comment)
        test_func(root, elem2, 1)
        assert list(root) == [elem1, elem3, elem2._comment, elem2]
        test_func(root, elem2, -2)
        assert list(root) == [elem2._comment, elem2, elem1, elem3]

    def test_copy(self):
        test_func = tree.FomodElement.__copy__
        ElementTest.__copy__ = tree.FomodElement.__copy__
        ElementTest.__deepcopy__ = mock_copy = mock.Mock()

        elem = make_element('a')
        test_func(elem)
        mock_copy.assert_called_once()

    def test_deepcopy_root(self):
        test_func = tree.FomodElement.__deepcopy__
        ElementTest._comment = None
        ElementTest.comment = tree.FomodElement.comment
        ElementTest.__deepcopy__ = tree.FomodElement.__deepcopy__

        # root with text
        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a' type='xs:string'/>"
                                  "</xs:schema>")
        elem = make_element('a')
        elem.text = 'text'
        elem.makeelement = make_element
        elem._schema_element = schema[0]
        assert_elem_eq(test_func(elem, None), elem)

        # child with grandchildren and comment
        schema = etree.fromstring("<xs:schema xmlns:xs='http://www"
                                  ".w3.org/2001/XMLSchema'>"
                                  "<xs:element name='a'>"
                                  "<xs:complexType>"
                                  "<xs:sequence>"
                                  "<xs:element name='b'>"
                                  "<xs:complexType>"
                                  "<xs:sequence>"
                                  "<xs:element name='c'/>"
                                  "<xs:element name='d'/>"
                                  "</xs:sequence>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "</xs:sequence>"
                                  "</xs:complexType>"
                                  "</xs:element>"
                                  "</xs:schema>")
        lookup = etree.ElementDefaultClassLookup(element=ElementTest)
        xml_parser = etree.XMLParser()
        xml_parser.set_element_class_lookup(lookup)
        root = etree.fromstring("<a><b><c/><d/></b></a>", xml_parser)
        elem = root[0]
        elem.makeelement = make_element
        elem._schema_element = schema[0][0][0][0]
        elem._comment = etree.Comment('comment')
        elem.addprevious(elem._comment)
        elem_c = elem[0]
        elem_c.makeelement = make_element
        elem_c._schema_element = schema[0][0][0][0][0][0][0]
        elem_d = elem[1]
        elem_d.makeelement = make_element
        elem_d._schema_element = schema[0][0][0][0][0][0][1]
        assert_elem_eq(test_func(elem, None), elem)


class TestRoot():
    def test_info_root(self):
        test_func = tree.Root.info_root.fget

        test_parser.info_root = 'success'

        assert test_func(test_parser.makeelement('a')) == 'success'
