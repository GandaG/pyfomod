from copy import copy, deepcopy

from lxml import etree

import mock
import pyfomod
import pytest
from pyfomod import parser

# tests that need a modifiable tree should use schema_mod fixture and
# get the schema directly from pyfomod instead of using this variable
fomod_schema = pyfomod.FOMOD_SCHEMA_TREE


def assert_elem_eq(e1, e2):
    if (e1.tag != e2.tag or
            e1.text != e2.text or
            e1.tail != e2.tail or
            e1.attrib != e2.attrib or
            len(e1) != len(e2)):
        raise AssertionError("The following elements are not equivalent:\n"
                             "tag: {}\ntext: {}\ntail: {}\n"
                             "attrib: {}\nchild_num: {}\n\n"
                             "tag: {}\ntext: {}\ntail: {}\n"
                             "attrib: {}\nchild_num: {}"
                             "".format(e1.tag, e1.text,
                                       e1.tail, e1.attrib,
                                       len(e1), e2.tag,
                                       e2.text, e2.tail,
                                       e2.attrib, len(e2)))
    for c1, c2 in zip(e1, e2):
        assert_elem_eq(c1, c2)


class Test_FomodElement:
    def test_element_get_max_occurs_normal(self, simple_parse):
        root = simple_parse[0]
        assert root._element_get_max_occurs(root._schema_element) == 1

    def test_element_get_max_occurs_unbounded(self, simple_parse):
        file_d = simple_parse[1][2][1]
        assert file_d._element_get_max_occurs(file_d._schema_element) is None

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

    def test_comment_get_none(self, simple_parse):
        name = simple_parse[1][0]
        assert name.comment == ""

    def test_comment_get_normal(self, simple_parse):
        name = simple_parse[0][1]
        assert name.comment == " The name of the mod "

    def test_comment_set_none(self, conf_tree):
        name = conf_tree[0]
        assert name._comment is None
        name.comment = "comment"
        assert name.comment == "comment"

    def test_comment_set_normal(self, info_tree):
        name = info_tree[1]
        assert name.comment == " The name of the mod "
        name.comment = "comment"
        assert name.comment == "comment"

    def test_doc_normal(self, simple_parse):
        config = simple_parse[1]
        assert config.doc == "The main element containing the " \
            "module configuration info."

    def test_doc_none(self, simple_parse, schema_mod):
        config = simple_parse[1]
        config._schema_element.remove(config._schema_element[0])
        assert config.doc == ""

    def test_get_schema_doc_normal(self):
        doc = fomod_schema[-1][0][0].text
        assert parser.FomodElement._get_schema_doc(fomod_schema[-1]) == doc

    def test_get_schema_doc_none(self):
        assert parser.FomodElement._get_schema_doc(fomod_schema) is None

    def test_init_schema(self, simple_parse):
        for elem in simple_parse[0].iter(tag=etree.Element):
            assert elem._schema is pyfomod.FOMOD_SCHEMA_TREE

    def test_init_comment(self, simple_parse):
        name = simple_parse[0][1]
        assert name._comment is simple_parse[0][0]

    def test_get_order_from_group(self):
        group_elem = fomod_schema[4][1]
        result = parser.FomodElement._get_order_from_group(fomod_schema[5][1],
                                                           fomod_schema)
        assert group_elem is result

    def test_lookup_element_private_complex_type(self, simple_parse):
        root = simple_parse[0]
        current_lookups = (root._schema_element,
                           root._schema_type)
        assert current_lookups[0] is fomod_schema[-1]
        assert current_lookups[1] is fomod_schema[-1][1]

    def test_lookup_element_simple_element(self, simple_parse):
        name = simple_parse[0][1]
        current_lookups = (name._schema_element,
                           name._schema_type)
        assert current_lookups[0] is fomod_schema[-1][1][0][0]
        assert current_lookups[1] is fomod_schema[-1][1][0][0]

    def test_lookup_element_separate_complex_type(self, simple_parse):
        config = simple_parse[1]
        current_lookups = (config._schema_element,
                           config._schema_type)
        assert current_lookups[0] is fomod_schema[-2]
        assert current_lookups[1] is fomod_schema[-3]

    def test_lookup_element_group_order_tags(self, simple_parse):
        file_dep = simple_parse[1][2][1]
        current_lookups = (file_dep._schema_element,
                           file_dep._schema_type)
        assert current_lookups[0] is fomod_schema[4][1][0][0]
        assert current_lookups[1] is fomod_schema[2]

    def test_valid_attributes_simple_string(self, simple_parse):
        # a simple string attribute
        machine_version_attr = parser._Attribute("MachineVersion", None, None,
                                                 "string", "optional", None)
        version_elem = simple_parse[0][5]
        assert version_elem.valid_attributes() == [machine_version_attr]

    def test_valid_attributes_restriction(self, simple_parse):
        # fileDependency element (enumeration)
        state_rest_list = [parser._AttrRestElement('Missing',
                                                   "Indicates the mod file is"
                                                   " not installed."),
                           parser._AttrRestElement('Inactive', "Indicates the"
                                                   " mod file is installed, "
                                                   "but not active."),
                           parser._AttrRestElement('Active', "Indicates the "
                                                   "mod file is installed and"
                                                   " active.")]
        state_restrictions = parser._AttrRestriction('enumeration ',
                                                     state_rest_list,
                                                     None, None, None, None,
                                                     None, None, None, None,
                                                     None, None)
        file_dep_attrs = [parser._Attribute("file", "The file of the mod upon "
                                            "which a the plugin depends.",
                                            None, "string", "required", None),
                          parser._Attribute("state", "The state of the mod "
                                            "file.", None, "string",
                                            "required", state_restrictions)]
        file_dep_elem = simple_parse[1][2][1]
        assert file_dep_elem.valid_attributes() == file_dep_attrs

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

    def test_set_attribute_normal(self, conf_tree):
        name = conf_tree[0]
        name.set_attribute('position', 'Right')
        assert name.get_attribute('position') == 'Right'

    def test_set_attribute_enum_restriction(self, conf_tree):
        name = conf_tree[0]
        with pytest.raises(ValueError):
            name.set_attribute('position', 'Top')

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
        parse_order = parser.FomodElement._valid_children_parse_order
        sequence_ord = self.composite_dependency_valid_children()
        assert parse_order(fomod_schema[4][1]) == sequence_ord

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

    @mock.patch('pyfomod.parser.FomodElement._init')
    def test_setup_shallow_schema_and_self_simple_elem(self, mock_init):
        schema = etree.fromstring("<schema xmlns='a'>"
                                  "<element name='elem'>"
                                  "<complexType/>"
                                  "</element>"
                                  "</schema>")
        elem = parser.FomodElement()
        elem.tag = 'elem'
        elem._schema_element = schema[0]
        elem._schema_type = schema[0]
        result = elem._setup_shallow_schema_and_self()
        assert_elem_eq(result[0], schema)
        assert_elem_eq(result[1], elem)

    @mock.patch('pyfomod.parser.FomodElement._init')
    def test_setup_shallow_schema_and_self_complex_separate(self, mock_init):
        schema = etree.fromstring("<xs:schema xmlns:xs='a'>"
                                  "<xs:element name='elem' type='elemtype'/>"
                                  "<xs:complexType name='elemtype'>"
                                  "<xs:sequence>"
                                  "<xs:element name='child1'/>"
                                  "<xs:element name='child2'/>"
                                  "<xs:element name='child3'/>"
                                  "</xs:sequence>"
                                  "</xs:complexType>"
                                  "</xs:schema>")
        elem = parser.FomodElement()
        elem.tag = 'elem'
        elem._schema_element = schema[0]
        elem._schema_type = schema[1]
        etree.SubElement(elem, 'child1')
        etree.SubElement(elem, 'child2')
        etree.SubElement(elem, 'child3')
        result = elem._setup_shallow_schema_and_self()
        assert_elem_eq(result[0], schema)
        assert_elem_eq(result[1], elem)

    @mock.patch('pyfomod.parser.FomodElement._init')
    def test_setup_shallow_schema_and_self_complex_below(self, mock_init):
        schema = etree.fromstring("<xs:schema xmlns:xs='a'>"
                                  "<xs:element name='elem'>"
                                  "<xs:complexType><xs:sequence>"
                                  "<xs:element name='child1'/>"
                                  "<xs:element name='child2'/>"
                                  "<xs:element name='child3'/>"
                                  "</xs:sequence></xs:complexType>"
                                  "</xs:element>"
                                  "</xs:schema>")
        elem = parser.FomodElement()
        elem.tag = 'elem'
        elem._schema_element = schema[0]
        elem._schema_type = schema[0][0]
        etree.SubElement(elem, 'child1')
        etree.SubElement(elem, 'child2')
        etree.SubElement(elem, 'child3')
        result = elem._setup_shallow_schema_and_self()
        assert_elem_eq(result[0], schema)
        assert_elem_eq(result[1], elem)

    def test_find_possible_index_typerror(self):
        test_func = parser.FomodElement._find_possible_index
        with pytest.raises(TypeError):
            # the second arg is any type other than string or FomodElement
            mock_self = mock.Mock(spec=parser.FomodElement)
            test_func(mock_self, 0)

    def test_find_possible_index_none(self):
        test_func = parser.FomodElement._find_possible_index
        test_tag = 'test'
        schema = etree.fromstring("<schema "
                                  "xmlns='http://www.w3.org/2001/XMLSchema'>"
                                  "<element name='elem'>"
                                  "<complexType/>"
                                  "</element>"
                                  "</schema>")
        elem = etree.Element('elem')
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_self._setup_shallow_schema_and_self.return_value = (schema, elem)
        assert test_func(mock_self, test_tag) is None
        with mock.patch('pyfomod.parser.FomodElement._init'):
            f_elem = parser.FomodElement()
            f_elem.tag = test_tag
            assert test_func(mock_self, f_elem) is None

    def test_find_possible_index_last(self):
        test_func = parser.FomodElement._find_possible_index
        test_tag = 'test'
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
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_self._setup_shallow_schema_and_self.return_value = (schema, elem)
        assert test_func(mock_self, test_tag) == -1
        # a reset is needed because elem was modified
        elem = etree.Element('elem')
        mock_self._setup_shallow_schema_and_self.return_value = (schema, elem)
        with mock.patch('pyfomod.parser.FomodElement._init'):
            f_elem = parser.FomodElement()
            f_elem.tag = test_tag
            assert test_func(mock_self, f_elem) == -1

    def test_find_possible_index_mid(self):
        test_func = parser.FomodElement._find_possible_index
        test_tag = 'child2'
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
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_self._setup_shallow_schema_and_self.return_value = (schema, elem)
        assert test_func(mock_self, test_tag) == 1
        # a reset is needed because elem was modified
        elem = etree.Element('elem')
        etree.SubElement(elem, 'child1')
        etree.SubElement(elem, 'child3')
        mock_self._setup_shallow_schema_and_self.return_value = (schema, elem)
        with mock.patch('pyfomod.parser.FomodElement._init'):
            f_elem = parser.FomodElement()
            f_elem.tag = test_tag
            assert test_func(mock_self, f_elem) == 1

    def test_can_add_child(self):
        info = etree.fromstring("<fomod><Name/></fomod>",
                                parser=parser.FOMOD_PARSER)
        assert info.can_add_child('Author')
        assert not info.can_add_child('Name')

    def test_can_remove_child_error(self):
        test_func = parser.FomodElement.can_remove_child
        with pytest.raises(TypeError):
            # second arg is anything but FomodElement
            mock_self = mock.Mock(spec=parser.FomodElement)
            test_func(mock_self, 0)
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_self.__iter__.return_value = []
        mock_child = mock.MagicMock(spec=parser.FomodElement)
        with pytest.raises(ValueError):
            test_func(mock_self, mock_child)

    def test_can_remove_child_normal(self):
        test_func = parser.FomodElement.can_remove_child
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
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_child = mock.MagicMock(spec=parser.FomodElement)
        mock_self.__contains__ = lambda y, x: True if x is mock_child \
            else False
        mock_self._setup_shallow_schema_and_self.return_value = (schema, elem)
        mock_self.index.return_value = 1
        assert not test_func(mock_self, mock_child)

    def test_can_replace_child_error(self):
        test_func = parser.FomodElement.can_replace_child
        with pytest.raises(TypeError):
            # second arg is anything but FomodElement
            mock_self = mock.Mock(spec=parser.FomodElement)
            test_func(mock_self, 0, 0)
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_old = mock.MagicMock(spec=parser.FomodElement)
        mock_new = mock.MagicMock(spec=parser.FomodElement)
        with pytest.raises(ValueError):
            test_func(mock_self, mock_old, mock_new)

    def test_can_replace_child_normal(self):
        test_func = parser.FomodElement.can_replace_child
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
            if x in (mock_old, mock_new) else False
        mock_self._setup_shallow_schema_and_self.return_value = (schema, elem)
        mock_self.index.return_value = 0
        assert test_func(mock_self, mock_old, mock_new)

    def test_can_copy_child_error(self):
        test_func = parser.FomodElement.can_copy_child
        with pytest.raises(TypeError):
            # second arg is anything but FomodElement
            mock_self = mock.Mock(spec=parser.FomodElement)
            test_func(mock_self, 0, 0)
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_child = mock.MagicMock(spec=parser.FomodElement)
        with pytest.raises(ValueError):
            test_func(mock_self, mock_child, None)

    def test_can_copy_child_normal(self):
        test_func = parser.FomodElement.can_copy_child
        mock_child = mock.MagicMock(spec=parser.FomodElement)
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_self.__contains__ = lambda y, x: True \
            if x is mock_child else False
        mock_parent = mock.MagicMock(spec=parser.FomodElement)
        mock_parent.can_add_child.return_value = True
        assert test_func(mock_self, mock_child, mock_parent)

    def test_can_move_child_error(self):
        test_func = parser.FomodElement.can_move_child
        with pytest.raises(TypeError):
            # second arg is anything but FomodElement
            mock_self = mock.Mock(spec=parser.FomodElement)
            test_func(mock_self, 0, 0)
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_child = mock.MagicMock(spec=parser.FomodElement)
        with pytest.raises(ValueError):
            test_func(mock_self, mock_child, None)

    def test_can_move_child_normal(self):
        test_func = parser.FomodElement.can_move_child
        mock_child = mock.MagicMock(spec=parser.FomodElement)
        mock_self = mock.MagicMock(spec=parser.FomodElement)
        mock_self.__contains__ = lambda y, x: True \
            if x is mock_child else False
        mock_self.can_remove_child.return_value = True
        mock_parent = mock.MagicMock(spec=parser.FomodElement)
        mock_parent.can_add_child.return_value = True
        assert test_func(mock_self, mock_child, mock_parent)

    def test_copy(self):
        root = etree.fromstring("<fomod attr='1'>text</fomod>",
                                parser=parser.FOMOD_PARSER)
        root_copy = copy(root)
        root_deep = deepcopy(root)
        assert root.tag == root_copy.tag == root_deep.tag
        assert root.text == root_copy.text == root_deep.text
        assert root.tail == root_copy.tail == root_deep.tail
        assert root.nsmap == root_copy.nsmap == root_deep.nsmap
        assert root.attrib == root_copy.attrib == root_deep.attrib

    def test_deepcopy_root(self):
        root = etree.fromstring("<fomod attr='1'/>",
                                parser=parser.FOMOD_PARSER)
        root_copy = deepcopy(root)
        assert root.tag == root_copy.tag
        assert root.text == root_copy.text
        assert root.tail == root_copy.tail
        assert root.nsmap == root_copy.nsmap
        assert root.attrib == root_copy.attrib

    def test_deepcopy_child(self):
        child = etree.fromstring("<fomod><Name>text</Name>tail</fomod>",
                                 parser=parser.FOMOD_PARSER)[0]
        child_copy = deepcopy(child)
        assert child.tag == child_copy.tag
        assert child.text == child_copy.text
        assert child.tail == child_copy.tail
        assert child.nsmap == child_copy.nsmap
        assert child.attrib == child_copy.attrib

    def test_deepcopy_children(self):
        root = etree.fromstring("<fomod><Name/><Author/><Version/></fomod>",
                                parser=parser.FOMOD_PARSER)
        root_copy = deepcopy(root)
        assert len(root) == len(root_copy)
        for index in range(0, len(root)):
            assert root[index].tag == root_copy[index].tag
            assert root[index].text == root_copy[index].text
            assert root[index].tail == root_copy[index].tail
            assert root[index].nsmap == root_copy[index].nsmap
            assert root[index].attrib == root_copy[index].attrib


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
