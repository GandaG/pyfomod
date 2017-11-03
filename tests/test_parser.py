from lxml import etree

import mock
import pyfomod
import pytest
from helpers import ElementTest, assert_elem_eq, make_element
from pyfomod import parser

# tests that need a modifiable tree should use schema_mod fixture and
# get the schema directly from pyfomod instead of using this variable
fomod_schema = pyfomod.FOMOD_SCHEMA_TREE


class Test_FomodElement:
    def test_max_occ_default_value(self, simple_parse):
        root = simple_parse[0]
        assert root.max_occurences == 1

    def test_max_occ_unbounded(self, simple_parse):
        file_dep = simple_parse[1][2][1]
        assert file_dep.max_occurences is None

    def test_min_occ_default_value(self, simple_parse):
        root = simple_parse[1]
        assert root.min_occurences == 1

    def test_min_occ_normal_value(self, simple_parse):
        file_dep = simple_parse[1][2]
        assert file_dep.min_occurences == 0

    def test_type_none(self, simple_parse):
        root = simple_parse[0]
        assert root.type is None

    def test_type_simple_element(self, simple_parse):
        name = simple_parse[0][1]
        assert name.type == 'string'

    def test_type_complex_element(self, simple_parse):
        version = simple_parse[0][5]
        assert version.type == 'string'

    def test_comment_get_none(self):
        test_func = parser.FomodElement.comment.fget
        elem = ElementTest()
        elem._comment = None
        assert test_func(elem) == ""

    def test_comment_get_normal(self):
        test_func = parser.FomodElement.comment.fget
        elem = ElementTest()
        elem._comment = etree.Comment('comment')
        assert test_func(elem) == "comment"

    def test_comment_set_none(self):
        test_func = parser.FomodElement.comment.fset
        parent = ElementTest()
        elem = ElementTest()
        parent.append(elem)
        elem._comment = None
        test_func(elem, None)
        assert elem._comment is None
        elem._comment = etree.Comment('comment')
        parent.insert(0, elem._comment)
        test_func(elem, None)
        assert elem._comment is None

    def test_comment_set_normal(self):
        test_func = parser.FomodElement.comment.fset
        elem = ElementTest()
        elem._comment = None
        test_func(elem, "comment")
        assert elem._comment.text == "comment"
        elem._comment = etree.Comment('comment')
        test_func(elem, "test")
        assert elem._comment.text == "test"

    def test_doc_normal(self, simple_parse):
        config = simple_parse[1]
        assert config.doc == "The main element containing the " \
            "module configuration info."

    def test_doc_none(self, simple_parse, schema_mod):
        config = simple_parse[1]
        config._schema_element.remove(config._schema_element[0])
        assert config.doc == ""

    def test_init_schema(self, simple_parse):
        for elem in simple_parse[0].iter(tag=etree.Element):
            assert elem._schema is pyfomod.FOMOD_SCHEMA_TREE

    def test_init_comment(self, simple_parse):
        name = simple_parse[0][1]
        assert name._comment is simple_parse[0][0]

    def test_shallow_copy_element(self):
        elem_orig = etree.fromstring('<elem a="1">text</elem>')
        elem_copy = parser.FomodElement._copy_element(elem_orig)
        assert_elem_eq(elem_orig, elem_copy)

    def test_deep_copy_element(self):
        elem_orig = etree.fromstring('<elem a="1">text<child/>tail</elem>')
        elem_copy = parser.FomodElement._copy_element(elem_orig, -1)
        assert_elem_eq(elem_orig, elem_copy)

    def test_lookup_element_private_complex_type(self, simple_parse):
        root = simple_parse[0]
        assert root._schema_element is fomod_schema[-1]

    def test_lookup_element_simple_element(self, simple_parse):
        name = simple_parse[0][1]
        assert name._schema_element is fomod_schema[-1][1][0][0]

    def test_lookup_element_separate_complex_type(self, simple_parse):
        config = simple_parse[1]
        assert config._schema_element is fomod_schema[-2]

    def test_lookup_element_group_order_tags(self, simple_parse):
        file_dep = simple_parse[1][2][1]
        assert file_dep._schema_element is fomod_schema[4][1][0][0]

    def test_valid_attributes(self):
        test_func = parser.FomodElement.valid_attributes

        # simple element - no attributes
        schema = etree.fromstring("<element name='a' type='xs:string'/>")
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self._schema_element = schema
        assert test_func(mock_self) == []

        # a simple string attribute
        schema = etree.fromstring("<element name='a'>"
                                  "<complexType>"
                                  "<attribute name='attr' type='xs:string'/>"
                                  "</complexType>"
                                  "</element>")
        expected = parser._Attribute("attr", None, None,
                                     "string", "optional", None)
        mock_self._schema_element = schema
        assert test_func(mock_self) == [expected]

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
        rest_list = [parser._AttrRestElement('aa',
                                             "Enumeration documentation."),
                     parser._AttrRestElement('bb', None)]
        attr_rest = parser._AttrRestriction('enumeration ', rest_list,
                                            None, None, None, None, None,
                                            None, None, None, None, None)
        child_rest = parser._AttrRestriction('', [],
                                             None, None, None, None, None,
                                             None, None, None, None, None)
        expected = [parser._Attribute('attr', "Attribute documentation.",
                                      None, 'string', 'optional', attr_rest),
                    parser._Attribute('child', None, None, 'other_attr',
                                      'optional', child_rest)]
        mock_self._schema_element = schema
        assert test_func(mock_self) == expected

    def test_required_attributes(self):
        attr1 = parser._Attribute("attr1", None, None,
                                  "string", "optional", None)
        attr2 = parser._Attribute("attr2", None, None,
                                  "string", "required", None)
        attr3 = parser._Attribute("attr3", None, None,
                                  "string", "optional", None)
        attr4 = parser._Attribute("attr4", None, None,
                                  "string", "required", None)
        self_mock = mock.Mock(spec=parser.FomodElement)
        self_mock.valid_attributes.return_value = [attr1, attr2, attr3, attr4]
        assert parser.FomodElement.required_attributes(self_mock) == [attr2,
                                                                      attr4]

    def test_find_valid_attribute_normal(self, simple_parse):
        version = simple_parse[0][5]
        attr = parser._Attribute('MachineVersion', None, None,
                                 'string', 'optional', None)
        assert version._find_valid_attribute('MachineVersion') == attr

    def test_find_valid_attribute_valueerror(self, simple_parse):
        name = simple_parse[0][1]
        with pytest.raises(ValueError):
            name._find_valid_attribute('anyAttribute')

    def test_get_attribute_existing(self, simple_parse):
        mod_dep = simple_parse[1][2]
        assert mod_dep.get_attribute('operator') == 'And'

    def test_get_attribute_default(self, simple_parse):
        name = simple_parse[1][0]
        assert name.get_attribute('position') == 'Left'

    def test_set_attribute(self):
        test_func = parser.FomodElement.set_attribute
        ElementTest._find_valid_attribute = \
            parser.FomodElement._find_valid_attribute
        ElementTest.valid_attributes = parser.FomodElement.valid_attributes
        ElementTest._copy_element = parser.FomodElement._copy_element

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

    def composite_dependency_valid_children(self):
        file_dep_child = parser._ChildElement('fileDependency', None, 1)
        flag_dep_child = parser._ChildElement('flagDependency', None, 1)
        game_dep_child = parser._ChildElement('gameDependency', 1, 0)
        fomm_dep_child = parser._ChildElement('fommDependency', 1, 0)
        dep_child = parser._ChildElement('dependencies', 1, 1)
        choice_ord = parser._OrderIndicator('choice',
                                            [file_dep_child, flag_dep_child,
                                             game_dep_child, fomm_dep_child,
                                             dep_child],
                                            None, 1)
        return parser._OrderIndicator('sequence', [choice_ord], 1, 1)

    def test_valid_children_parse_order(self):
        test_func = parser.FomodElement._valid_children_parse_order
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
        all_ord = parser._OrderIndicator('all',
                                         [parser._ChildElement('c', 1, 1)],
                                         1, 1)
        choice_ord = parser._OrderIndicator('choice', [all_ord], 1, 0)
        expected = parser._OrderIndicator('sequence',
                                          [parser._ChildElement('a', 1, 1),
                                           choice_ord,
                                           parser._ChildElement(None, 10, 2)],
                                          3, 1)
        assert test_func(schema[0]) == expected

    def test_valid_children_group_and_order(self, simple_parse):
        mod_dep = simple_parse[1][2]
        sequence_ord = self.composite_dependency_valid_children()
        assert mod_dep.valid_children() == sequence_ord

    def test_valid_children_none(self, simple_parse):
        name = simple_parse[0][1]
        assert name.valid_children() is None

    def test_required_children_choice_none(self):
        test_func = parser.FomodElement._required_children_choice
        test_choice = parser._OrderIndicator('choice', [], 2, 2)
        mock_self = mock.Mock(spec=parser.FomodElement)
        assert test_func(mock_self, test_choice) == []

    def test_required_children_choice_elem(self):
        test_func = parser.FomodElement._required_children_choice
        test_child = parser._ChildElement('child', 2, 2)
        test_choice = parser._OrderIndicator('choice', [test_child], 2, 2)
        mock_self = mock.Mock(spec=parser.FomodElement)
        assert test_func(mock_self, test_choice) == [('child', 4)]

    def test_required_children_choice_choice(self):
        test_func = parser.FomodElement._required_children_choice
        test_choice2 = mock.Mock(spec=parser._OrderIndicator)
        test_choice2.type = 'choice'
        test_choice = parser._OrderIndicator('choice', [test_choice2], 2, 2)
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self._required_children_choice.return_value = [('child', 2)]
        assert test_func(mock_self, test_choice) == [('child', 4)]
        assert mock_self._required_children_choice.called

    def test_required_children_choice_sequence(self):
        test_func = parser.FomodElement._required_children_choice
        test_sequence = mock.Mock(spec=parser._OrderIndicator)
        test_sequence.type = 'sequence'
        test_choice = parser._OrderIndicator('choice', [test_sequence], 2, 2)
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self._required_children_sequence.return_value = [('child', 2)]
        assert test_func(mock_self, test_choice) == [('child', 4)]
        assert mock_self._required_children_sequence.called

    def test_required_children_sequence_none(self):
        test_func = parser.FomodElement._required_children_sequence
        test_sequence = parser._OrderIndicator('sequence', [], 2, 2)
        mock_self = mock.Mock(spec=parser.FomodElement)
        assert test_func(mock_self, test_sequence) == []

    def test_required_children_sequence_elem(self):
        test_func = parser.FomodElement._required_children_sequence
        test_child = mock.Mock(spec=parser._ChildElement)
        test_child.tag = 'child'
        test_child.min_occ = 5
        test_sequence = parser._OrderIndicator('sequence', [test_child], 2, 2)
        mock_self = mock.Mock(spec=parser.FomodElement)
        assert test_func(mock_self, test_sequence) == [('child', 10)]

    def test_required_children_sequence_choice(self):
        test_func = parser.FomodElement._required_children_sequence
        test_choice = mock.Mock(spec=parser._OrderIndicator)
        test_choice.type = 'choice'
        test_sequence = parser._OrderIndicator('sequence', [test_choice], 2, 2)
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self._required_children_choice.return_value = [('child', 2)]
        assert test_func(mock_self, test_sequence) == [('child', 4)]
        assert mock_self._required_children_choice.called

    def test_required_children_sequence_sequence(self):
        test_func = parser.FomodElement._required_children_sequence
        test_sequence = mock.Mock(spec=parser._OrderIndicator)
        test_sequence.type = 'sequence'
        test_sequence = parser._OrderIndicator('sequence', [test_sequence],
                                               2, 2)
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self._required_children_sequence.return_value = [('child', 2)]
        assert test_func(mock_self, test_sequence) == [('child', 4)]
        assert mock_self._required_children_sequence.called

    def test_required_children_none(self):
        test_func = parser.FomodElement.required_children
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self.valid_children.return_value = None
        assert test_func(mock_self) == []

    def test_required_children_choice(self):
        test_func = parser.FomodElement.required_children
        test_choice = mock.Mock(spec=parser._OrderIndicator)
        test_choice.type = 'choice'
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self.valid_children.return_value = test_choice
        mock_self._required_children_choice.return_value = [('child', 2)]
        assert test_func(mock_self) == [('child', 2)]
        mock_self._required_children_choice.assert_called_once_with(
            test_choice)

    def test_required_children_sequence(self):
        test_func = parser.FomodElement.required_children
        test_sequence = mock.Mock(spec=parser._OrderIndicator)
        test_sequence.type = 'sequence'
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self.valid_children.return_value = test_sequence
        mock_self._required_children_sequence.return_value = [('child', 2)]
        assert test_func(mock_self) == [('child', 2)]
        mock_self._required_children_sequence.assert_called_once_with(
            test_sequence)

    @mock.patch('pyfomod.parser.copy_schema')
    def test_find_possible_index(self, mock_schema):
        test_func = parser.FomodElement._find_possible_index

        # not valid
        test_tag = 'test'
        schema = etree.fromstring("<schema "
                                  "xmlns='http://www.w3.org/2001/XMLSchema'>"
                                  "<element name='elem'>"
                                  "<complexType/>"
                                  "</element>"
                                  "</schema>")
        elem = etree.Element('elem')
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_self._schema_element = mock.Mock(spec=ElementTest)
        mock_self._copy_element.return_value = elem
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
        mock_self._copy_element.return_value = elem
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
        mock_self._copy_element.return_value = elem
        mock_schema.return_value = schema
        assert test_func(mock_self, test_tag) == 1

    def test_can_add_child_typerror(self):
        test_func = parser.FomodElement.can_add_child
        with pytest.raises(TypeError):
            # the second arg is any type other than string or FomodElement
            mock_self = mock.Mock(spec=parser.FomodElement)
            test_func(mock_self, 0)

    def test_can_add_child(self):
        test_func = parser.FomodElement.can_add_child
        mock_self = mock.Mock(spec=parser.FomodElement)
        # Any value will work for this return_value
        mock_self._find_possible_index.return_value = 0
        mock_parent = mock.Mock(spec=parser.FomodElement)
        mock_child = mock.Mock(spec=parser.FomodElement)
        mock_child.getparent.return_value = mock_parent
        mock_parent.can_remove_child = lambda x: True \
            if x is mock_child else False
        assert test_func(mock_self, mock_child)
        mock_parent.can_remove_child = lambda x: False \
            if x is mock_child else True
        assert not test_func(mock_self, mock_child)
        mock_tag = mock.Mock(spec=str)
        mock_self._find_possible_index.return_value = None
        assert not test_func(mock_self, mock_tag)

    def test_add_child_error(self):
        test_func = parser.FomodElement.add_child

        mock_self = mock.Mock(spec=parser.FomodElement)
        with pytest.raises(TypeError):
            test_func(mock_self, 0)

        mock_self._find_possible_index.return_value = None
        mock_child = mock.Mock(spec=parser.FomodElement)
        mock_child.tag = "a"
        with pytest.raises(ValueError):
            test_func(mock_self, mock_child)

    @mock.patch('lxml.etree.SubElement')
    def test_setup_new_element(self, mock_subelem):
        test_func = parser.FomodElement._setup_new_element
        mock_self = mock.Mock(spec=parser.FomodElement)
        attr_rest = parser._AttrRestriction('enumeration',
                                            [parser._AttrRestElement('enum',
                                                                     None)],
                                            *[None] * 10)
        req_attr = [parser._Attribute('attr_default',
                                      None,
                                      'default',
                                      None,
                                      'required',
                                      None),
                    parser._Attribute('attr_rest',
                                      None,
                                      None,
                                      None,
                                      'required',
                                      attr_rest),
                    parser._Attribute('attr_none',
                                      None,
                                      None,
                                      None,
                                      'required',
                                      None)]
        mock_self.required_attributes.return_value = req_attr
        mock_self.required_children.return_value = [('child1', 1),
                                                    ('child2', 7),
                                                    ('child3', 2)]
        test_func(mock_self)
        attr_calls = [mock.call('attr_default', 'default'),
                      mock.call('attr_rest', 'enum'),
                      mock.call('attr_none', '')]
        mock_self.set_attribute.assert_has_calls(attr_calls)
        setup_calls = [mock.call()._setup_new_element()] * 10
        subelem_calls = ([mock.call(mock_self, 'child1')] +
                         [mock.call(mock_self, 'child2')] * 7 +
                         [mock.call(mock_self, 'child3')] * 2)
        child_calls = [j for i in zip(subelem_calls, setup_calls) for j in i]
        mock_subelem.assert_has_calls(child_calls)

    @mock.patch('lxml.etree.SubElement')
    def test_add_child_str(self, mock_subelem):
        test_func = parser.FomodElement.add_child
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_tag = mock.Mock(spec=str)
        mock_child = mock_subelem.return_value
        mock_child._comment = None
        test_func(mock_self, mock_tag)
        mock_self._find_possible_index.assert_called_once_with(mock_tag)
        mock_subelem.assert_called_once_with(mock_self, mock_tag)
        mock_child._setup_new_element.assert_called_once()
        fpi_ret = mock_self._find_possible_index.return_value
        mock_self.insert.assert_called_once_with(fpi_ret, mock_child)

    def test_add_child_elem(self):
        test_func = parser.FomodElement.add_child
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_child = mock.Mock(spec=parser.FomodElement)
        mock_child._comment = mock.Mock(spec=etree._Comment)
        test_func(mock_self, mock_child)
        mock_self._find_possible_index.assert_called_once_with(mock_child.tag)
        mock_child.getparent.assert_called_once()
        parent = mock_child.getparent.return_value
        parent.remove_child.assert_called_once_with(mock_child)
        fpi_ret = mock_self._find_possible_index.return_value
        insert_calls = [mock.call(fpi_ret, mock_child),
                        mock.call(fpi_ret, mock_child._comment)]
        mock_self.insert.call_list(insert_calls)

    @mock.patch('pyfomod.parser.copy_schema')
    def test_can_remove_child(self, mock_schema):
        test_func = parser.FomodElement.can_remove_child

        # errors
        with pytest.raises(TypeError):
            # second arg is anything but FomodElement
            mock_self = mock.Mock(spec=parser.FomodElement)
            test_func(mock_self, 0)
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_self.__iter__.return_value = []
        mock_child = mock.MagicMock(spec=parser.FomodElement)
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
        mock_child = mock.MagicMock(spec=parser.FomodElement)
        mock_self.__contains__ = lambda y, x: True if x is mock_child \
            else False
        mock_self._schema_element = mock.Mock(spec=ElementTest)
        mock_self._copy_element.return_value = elem
        mock_schema.return_value = schema
        mock_self.index.return_value = 1
        assert not test_func(mock_self, mock_child)

    def test_remove_child_error(self):
        test_func = parser.FomodElement.remove_child
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self.can_remove_child.return_value = False
        with pytest.raises(ValueError):
            test_func(mock_self, 0)

    def test_remove_child_normal(self):
        test_func = parser.FomodElement.remove_child
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self.can_remove_child.return_value = True
        mock_child = mock.Mock(spec=parser.FomodElement)
        mock_comment = mock_child._comment = mock.Mock(spec=etree._Comment)
        test_func(mock_self, mock_child)
        mock_self.can_remove_child.assert_called_once_with(mock_child)
        remove_calls = [mock.call(mock_comment),
                        mock.call(mock_self)]
        mock_self.remove.call_list == remove_calls

    @mock.patch('pyfomod.parser.copy_schema')
    def test_can_replace_child(self, mock_schema):
        test_func = parser.FomodElement.can_replace_child

        # errors
        with pytest.raises(TypeError):
            # second arg is anything but FomodElement
            mock_self = mock.Mock(spec=parser.FomodElement)
            test_func(mock_self, 0, 0)
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_old = mock.MagicMock(spec=parser.FomodElement)
        mock_new = mock.MagicMock(spec=parser.FomodElement)
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
        mock_old = mock.MagicMock(spec=parser.FomodElement)
        mock_old.tag = 'child1'
        mock_new = mock.MagicMock(spec=parser.FomodElement)
        mock_new.tag = 'child2'
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_self.__contains__ = lambda y, x: True \
            if x is mock_old else False
        mock_self._schema_element = mock.Mock(spec=ElementTest)
        mock_self._copy_element.return_value = elem
        mock_schema.return_value = schema
        mock_self.index.return_value = 0
        mock_new.getparent.return_value = None
        assert test_func(mock_self, mock_old, mock_new)
        mock_parent = mock.Mock(spec=parser.FomodElement)
        mock_new.getparent.return_value = mock_parent
        mock_parent.can_remove_child = lambda x: False \
            if x is mock_new else True
        assert not test_func(mock_self, mock_old, mock_new)

    def test_replace_child_error(self):
        test_func = parser.FomodElement.replace_child
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self.can_replace_child.return_value = False
        with pytest.raises(ValueError):
            test_func(mock_self, 0, 0)

    def test_replace_child_normal(self):
        test_func = parser.FomodElement.replace_child
        mock_self = mock.Mock(spec=parser.FomodElement)
        mock_self.can_replace_child.return_value = True
        mock_old = mock.Mock(spec=parser.FomodElement)
        mock_old._comment = mock.Mock(spec=etree._Comment)
        mock_new = mock.Mock(spec=parser.FomodElement)
        mock_new._comment = mock.Mock(spec=etree._Comment)
        test_func(mock_self, mock_old, mock_new)
        mock_self.can_replace_child.assert_called_once_with(mock_old, mock_new)
        mock_new.getparent.assert_called_once()
        parent = mock_new.getparent.return_value
        parent.remove_child.assert_called_once_with(mock_new)
        mock_self.remove.assert_called_once_with(mock_old._comment)
        mock_self.insert.assert_called_once_with(mock_self.index.return_value,
                                                 mock_new._comment)
        mock_self.replace.assert_called_once_with(mock_old, mock_new)

    def test_copy(self):
        test_func = parser.FomodElement.__copy__
        ElementTest.__copy__ = parser.FomodElement.__copy__
        ElementTest.__deepcopy__ = mock_copy = mock.Mock()

        elem = make_element('a')
        test_func(elem)
        mock_copy.assert_called_once()

    def test_deepcopy_root(self):
        test_func = parser.FomodElement.__deepcopy__
        ElementTest._comment = None
        ElementTest.comment = parser.FomodElement.comment
        ElementTest.__deepcopy__ = parser.FomodElement.__deepcopy__

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


class Test_FomodLookup:
    def test_base_class(self, simple_parse):
        for tree in simple_parse:
            for element in tree.iter(tag=etree.Element):
                assert isinstance(element, parser.FomodElement)

    def test_subclasses(self, simple_parse):
        root = simple_parse[1]
        assert isinstance(root, parser.Root)
        mod_dep = root.findall('.//moduleDependencies')
        assert(all(isinstance(elem, parser.Dependencies)) for elem in mod_dep)
        dep = root.findall('.//dependencies')
        assert(all(isinstance(elem, parser.Dependencies)) for elem in dep)
        vis = root.findall('.//visible')
        assert(all(isinstance(elem, parser.Dependencies)) for elem in vis)
        step = root.findall('.//installStep')
        assert(all(isinstance(elem, parser.InstallStep)) for elem in step)
        group = root.findall('.//group')
        assert(all(isinstance(elem, parser.Group)) for elem in group)
        plugin = root.findall('.//plugin')
        assert(all(isinstance(elem, parser.Plugin)) for elem in plugin)
        tp_dep = root.findall('.//dependencyType')
        assert(all(isinstance(elem, parser.TypeDependency)) for elem in tp_dep)
        tp_pat = root.findall('.//pattern/type')
        assert(all(isinstance(elem, parser.TypePattern)) for elem in tp_pat)
        fl_pat = root.findall('.//pattern/files')
        assert(all(isinstance(elem, parser.InstallPattern)) for elem in fl_pat)
