import os

from lxml import etree
from pyfomod import parser, tree

import mock
from helpers import assert_elem_eq, test_parser


def test_new():
    test_func = parser.new

    expected_info = etree.fromstring("<fomod/>")
    expected_conf = etree.fromstring("<config xmlns:xsi='http://www.w3.org"
                                     "/2001/XMLSchema-instance' xsi:"
                                     "noNamespaceSchemaLocation='http://"
                                     "qconsulting.ca/fo3/ModConfig5.0.xsd'>"
                                     "<moduleName/></config>")

    root = test_func()
    assert_elem_eq(root, expected_conf)
    assert_elem_eq(root.info_root, expected_info)

    expected_conf = etree.fromstring("<config xmlns:xsi='http://www.w3.org"
                                     "/2001/XMLSchema-instance' xsi:"
                                     "noNamespaceSchemaLocation='https://"
                                     "github.com/fomod-lang/fomod/blob/5.0/"
                                     "ModuleConfig.xsd'>"
                                     "<moduleName/></config>")

    root = test_func(old_schema_link=False)
    assert_elem_eq(root, expected_conf)
    assert_elem_eq(root.info_root, expected_info)


def test_from_string():
    test_func = parser.from_string

    info_str = "<fomod/>\n"
    conf_str = "<config>\n  <moduleName/>\n</config>\n"

    tree = test_func(info_str, conf_str)
    assert_elem_eq(tree.info_root, etree.fromstring(info_str, test_parser))
    assert_elem_eq(tree, etree.fromstring(conf_str, test_parser))


def test_parse(tmpdir):
    test_func = parser.parse
    tmpdir = str(tmpdir)

    info_str = "<fomod/>\n"
    conf_str = "<config>\n  <moduleName/>\n</config>\n"

    fomod_path = os.path.join(tmpdir, 'fomod')
    info_path = os.path.join(fomod_path, "info.xml")
    conf_path = os.path.join(fomod_path, "ModuleConfig.xml")

    os.makedirs(fomod_path)
    with open(info_path, 'w') as info, open(conf_path, 'w') as conf:
        info.write(info_str)
        conf.write(conf_str)

    tree = test_func(tmpdir)
    assert_elem_eq(tree.info_root, etree.fromstring(info_str, test_parser))
    assert_elem_eq(tree, etree.fromstring(conf_str, test_parser))

    tree = test_func(fomod_path)
    assert_elem_eq(tree.info_root, etree.fromstring(info_str, test_parser))
    assert_elem_eq(tree, etree.fromstring(conf_str, test_parser))

    tree = test_func((info_path, conf_path))
    assert_elem_eq(tree.info_root, etree.fromstring(info_str, test_parser))
    assert_elem_eq(tree, etree.fromstring(conf_str, test_parser))


def test_to_string():
    test_func = parser.to_string

    xml_decl = b"<?xml version='1.0' encoding='utf-8'?>\n"
    info_str = b"<fomod/>\n"
    conf_str = b"<config>\n  <moduleName/>\n</config>\n"

    info_tree = etree.fromstring(info_str, test_parser)
    conf_tree = etree.fromstring(conf_str, test_parser)
    conf_tree.info_root = info_tree

    assert (xml_decl + info_str, xml_decl + conf_str) == test_func(conf_tree)


@mock.patch('pyfomod.parser.to_string')
def test_write(mock_to_string, tmpdir):
    test_func = parser.write
    tmpdir = str(tmpdir)

    xml_decl = b"<?xml version='1.0' encoding='utf-8'?>\n"
    info_str = b"<fomod/>\n"
    conf_str = b"<config>\n  <moduleName/>\n</config>\n"

    mock_to_string.return_value = (xml_decl + info_str,
                                   xml_decl + conf_str)

    fomod_path = os.path.join(tmpdir, 'fomod')
    info_path = os.path.join(fomod_path, "info.xml")
    conf_path = os.path.join(fomod_path, "ModuleConfig.xml")

    test_func("not needed, it's mocked", tmpdir)
    with open(info_path, 'rb') as info, open(conf_path, 'rb') as conf:
        assert info.read() == xml_decl + info_str
        assert conf.read() == xml_decl + conf_str

    os.remove(info_path)
    os.remove(conf_path)

    test_func("not needed, it's mocked", [info_path, conf_path])
    with open(info_path, 'rb') as info, open(conf_path, 'rb') as conf:
        assert info.read() == xml_decl + info_str
        assert conf.read() == xml_decl + conf_str


def test_speciallookup():
    """
    This class is tested as a single function
    because it has only one use case in its
    only function.
    """
    test_parser = etree.XMLParser()
    test_parser.set_element_class_lookup(parser.SpecialLookup())
    xml_frag = "<root><!--comment--><?processinst?><child/></root>"

    parsed = etree.fromstring(xml_frag, test_parser)
    assert isinstance(parsed, etree._Element)
    assert isinstance(parsed[0], etree.CommentBase)
    assert isinstance(parsed[1], etree.PIBase)
    assert isinstance(parsed[2], etree._Element)


@mock.patch('pyfomod.tree.FomodElement._lookup_element')
def test_fomodlookup(mock_lookup):
    """Same as above"""
    test_parser = etree.XMLParser()
    test_parser.set_element_class_lookup(parser.FomodLookup())
    xml_frag = ("<config>"
                "<dependencies/>"
                "<moduleDependencies/>"
                "<visible/>"
                "<installStep/>"
                "<group/>"
                "<plugin/>"
                "<dependencyType><unused><pattern/></unused></dependencyType>"
                "<conditionalFileInstalls><unused>"
                "<pattern/>"
                "</unused></conditionalFileInstalls>"
                "</config>")
    parsed = etree.fromstring(xml_frag, test_parser)
    assert isinstance(parsed, tree.Root)
    assert isinstance(parsed.find('dependencies'), tree.Dependencies)
    assert isinstance(parsed.find('moduleDependencies'), tree.Dependencies)
    assert isinstance(parsed.find('visible'), tree.Dependencies)
    assert isinstance(parsed.find('installStep'), tree.InstallStep)
    assert isinstance(parsed.find('group'), tree.Group)
    assert isinstance(parsed.find('plugin'), tree.Plugin)
    assert isinstance(parsed.find('dependencyType'), tree.TypeDependency)
    assert isinstance(parsed.find('conditionalFileInstalls/*/pattern'),
                      tree.InstallPattern)
    assert isinstance(parsed.find('dependencyType/*/pattern'),
                      tree.TypePattern)
