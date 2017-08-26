from lxml import etree

import pytest
from pyfomod import parser, validation

info_schema = validation.INFO_SCHEMA_TREE
conf_schema = validation.CONF_SCHEMA_TREE


class Test_FomodElement:
    def test_element_get_max_occurs_normal(self, simple_parse):
        root = simple_parse[0]
        root._setup(info_schema)
        root._lookup_element()
        assert root._element_get_max_occurs(root._schema_element) == 1

    def test_element_get_max_occurs_unbounded(self, simple_parse):
        file_d = simple_parse[1][2][1]
        file_d._setup(conf_schema)
        file_d._lookup_element()
        assert file_d._element_get_max_occurs(file_d._schema_element) is None

    def test_max_occ_default_value(self, simple_parse):
        root = simple_parse[0]
        root._setup(info_schema)
        root._lookup_element()
        assert root.max_occurences == 1

    def test_max_occ_unbounded(self, simple_parse):
        file_dep = simple_parse[1][2][1]
        file_dep._setup(conf_schema)
        file_dep._lookup_element()
        assert file_dep.max_occurences is None

    def test_min_occ_default_value(self, simple_parse):
        root = simple_parse[1]
        root._setup(conf_schema)
        root._lookup_element()
        assert root.min_occurences == 1

    def test_min_occ_normal_value(self, simple_parse):
        file_dep = simple_parse[1][2]
        file_dep._setup(conf_schema)
        file_dep._lookup_element()
        assert file_dep.min_occurences == 0

    def test_type_none(self, simple_parse):
        root = simple_parse[0]
        root._setup(info_schema)
        root._lookup_element()
        assert root.type is None

    def test_type_simple_element(self, simple_parse):
        name = simple_parse[0][1]
        name._setup(info_schema)
        name._lookup_element()
        assert name.type == 'string'

    def test_type_complex_element(self, simple_parse):
        version = simple_parse[0][5]
        version._setup(info_schema)
        version._lookup_element()
        assert version.type == 'string'

    def test_comment_get_none(self, simple_parse):
        name = simple_parse[1][0]
        name._setup(conf_schema)
        assert name.comment == ""

    def test_comment_get_normal(self, simple_parse):
        name = simple_parse[0][1]
        name._setup(info_schema)
        assert name.comment == " The name of the mod "

    def test_comment_set_none(self, conf_tree):
        name = conf_tree[0]
        name._setup(conf_schema)
        assert name._comment is None
        name.comment = "comment"
        assert name.comment == "comment"

    def test_comment_set_normal(self, info_tree):
        name = info_tree[1]
        name._setup(info_schema)
        assert name.comment == " The name of the mod "
        name.comment = "comment"
        assert name.comment == "comment"

    def std_cmp_elem(self):
        return etree.fromstring("<a boo=\"2\" goo=\"5\">text<b/>tail</a>",
                                parser=parser.FOMOD_PARSER)

    def test_compare_changed_order(self):
        elem_ord = etree.fromstring("<a goo=\"5\" boo=\"2\">text<b/>tail</a>",
                                    parser=parser.FOMOD_PARSER)
        assert elem_ord.compare(self.std_cmp_elem(), elem_ord)

    def test_compare_changed_attribute(self):
        elem_atr = etree.fromstring("<a boo=\"4\" goo=\"5\">text<b/>tail</a>",
                                    parser=parser.FOMOD_PARSER)
        assert not elem_atr.compare(self.std_cmp_elem(), elem_atr)

    def test_compare_changed_tail(self):
        elem_tail = etree.fromstring("<a boo=\"2\" goo=\"5\">text<b/>err</a>",
                                     parser=parser.FOMOD_PARSER)
        assert not elem_tail[0].compare(self.std_cmp_elem()[0], elem_tail[0])

    def test_compare_changed_text(self):
        elem_text = etree.fromstring("<a boo=\"2\" goo=\"5\">err<b/>tail</a>",
                                     parser=parser.FOMOD_PARSER)
        assert not elem_text.compare(self.std_cmp_elem(), elem_text)

    def test_compare_changed_tag(self):
        elem_tag = etree.fromstring("<c boo=\"2\" goo=\"5\">text<b/>tail</c>",
                                    parser=parser.FOMOD_PARSER)
        assert not elem_tag.compare(self.std_cmp_elem(), elem_tag)

    def test_compare_changed_children(self):
        elem_len = etree.fromstring("<a boo=\"2\" goo=\"5\">"
                                    "text<b/><c/>tail</a>",
                                    parser=parser.FOMOD_PARSER)
        assert not elem_len.compare(self.std_cmp_elem(), elem_len, True)

    def test_compare_changed_child_tag(self):
        elem_cld = etree.fromstring("<a boo=\"2\" goo=\"5\">text<c/>tail</a>",
                                    parser=parser.FOMOD_PARSER)
        assert not elem_cld.compare(self.std_cmp_elem(), elem_cld, True)

    def test_setup_schema(self, simple_parse):
        for elem in simple_parse[0].iter(tag=etree.Element):
            elem._setup(info_schema)
            assert parser.FomodElement.compare(elem._schema, info_schema)

    def test_setup_comment(self, simple_parse):
        name = simple_parse[0][1]
        name._setup(info_schema)
        assert parser.FomodElement.compare(name._comment, simple_parse[0][0])

    def test_get_order_from_group(self):
        group_elem = conf_schema[4][1]
        result = parser.FomodElement._get_order_from_group(conf_schema[5][1],
                                                           conf_schema)
        assert parser.FomodElement.compare(group_elem, result, True)

    def test_lookup_element_private_complex_type(self, simple_parse):
        root = simple_parse[0]
        root._setup(info_schema)
        root._lookup_element()
        current_lookups = (root._schema_element,
                           root._schema_type)
        assert parser.FomodElement.compare(current_lookups[0],
                                           info_schema[0])
        assert parser.FomodElement.compare(current_lookups[1],
                                           info_schema[0][1])

    def test_lookup_element_simple_element(self, simple_parse):
        name = simple_parse[0][1]
        name._setup(info_schema)
        name._lookup_element()
        current_lookups = (name._schema_element,
                           name._schema_type)
        assert parser.FomodElement.compare(current_lookups[0],
                                           info_schema[0][1][0][0])
        assert parser.FomodElement.compare(current_lookups[1],
                                           info_schema[0][1][0][0])

    def test_lookup_element_separate_complex_type(self, simple_parse):
        config = simple_parse[1]
        config._setup(conf_schema)
        config._lookup_element()
        current_lookups = (config._schema_element,
                           config._schema_type)
        assert parser.FomodElement.compare(current_lookups[0],
                                           conf_schema[-1])
        assert parser.FomodElement.compare(current_lookups[1],
                                           conf_schema[-2])

    def test_lookup_element_group_order_tags(self, simple_parse):
        file_dep = simple_parse[1][2][1]
        file_dep._setup(conf_schema)
        file_dep._lookup_element()
        current_lookups = (file_dep._schema_element,
                           file_dep._schema_type)
        assert parser.FomodElement.compare(current_lookups[0],
                                           conf_schema[4][1][0][0])
        assert parser.FomodElement.compare(current_lookups[1],
                                           conf_schema[2])

    def test_valid_attributes_simple_string(self, simple_parse):
        # a simple string attribute
        machine_version_attr = parser._Attribute("MachineVersion", None, None,
                                                 "string", "optional", None)
        version_elem = simple_parse[0][5]
        version_elem._setup(info_schema)
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
        file_dep_elem._setup(conf_schema)
        assert file_dep_elem.valid_attributes() == file_dep_attrs

    def test_find_valid_attribute_normal(self, simple_parse):
        version = simple_parse[0][5]
        version._setup(info_schema)
        version._lookup_element()
        attr = parser._Attribute('MachineVersion', None, None,
                                 'string', 'optional', None)
        assert version._find_valid_attribute('MachineVersion') == attr

    def test_find_valid_attribute_valueerror(self, simple_parse):
        name = simple_parse[0][1]
        name._setup(info_schema)
        name._lookup_element()
        with pytest.raises(ValueError):
            name._find_valid_attribute('anyAttribute')

    def test_get_attribute_existing(self, simple_parse):
        mod_dep = simple_parse[1][2]
        mod_dep._setup(conf_schema)
        mod_dep._lookup_element()
        assert mod_dep.get_attribute('operator') == 'And'

    def test_get_attribute_default(self, simple_parse):
        name = simple_parse[1][0]
        name._setup(conf_schema)
        name._lookup_element()
        assert name.get_attribute('position') == 'Left'

    def test_set_attribute_normal(self, conf_tree):
        name = conf_tree[0]
        name._setup(conf_schema)
        name._lookup_element()
        name.set_attribute('position', 'Right')
        assert name.get_attribute('position') == 'Right'

    def test_set_attribute_enum_restriction(self, conf_tree):
        name = conf_tree[0]
        name._setup(conf_schema)
        name._lookup_element()
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
        assert parse_order(conf_schema[4][1]) == sequence_ord

    def test_valid_children_group_and_order(self, simple_parse):
        mod_dep = simple_parse[1][2]
        mod_dep._setup(conf_schema)
        mod_dep._lookup_element()
        sequence_ord = self.composite_dependency_valid_children()
        assert mod_dep.valid_children() == sequence_ord

    def test_valid_children_none(self, simple_parse):
        name = simple_parse[0][1]
        name._setup(info_schema)
        name._lookup_element()
        assert name.valid_children() is None


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
