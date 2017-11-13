from lxml import etree

import mock
from pyfomod import parser, tree


def test_speciallookup():
    """
    This class is tested as a single function
    because it has only one use case in its
    only function.
    """
    test_parser = etree.XMLParser()
    test_parser.set_element_class_lookup(parser._SpecialLookup())
    xml_frag = "<root><!--comment--><?processinst?><child/></root>"

    parsed = etree.fromstring(xml_frag, test_parser)
    assert isinstance(parsed, etree._Element)
    assert isinstance(parsed[0], etree.CommentBase)
    assert isinstance(parsed[1], etree.PIBase)
    assert isinstance(parsed[2], etree._Element)


@mock.patch('pyfomod.tree.FomodElement._lookup_element')
def test_fomodlookup(mock_lookup):
    """Same as above"""
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
    parsed = etree.fromstring(xml_frag, parser.FOMOD_PARSER)
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
