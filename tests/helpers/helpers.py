from lxml import etree


class ElementTest(etree.ElementBase):
    """
    Use this class instead of simple etree.Element elements.
    This way you can add attributes to instances as you wish.
    """
    pass


class TestParser(etree.XMLParser):
    """
    Use this class instead of etree.XMLParser to add attributes
    as needed for testing.
    """
    pass


test_parser = TestParser(remove_blank_text=True)
test_parser.set_element_class_lookup(
        etree.ElementDefaultClassLookup(element=ElementTest))


def make_element(tag, text=None, attrib=None, nsmap=None):
    """Creates and returns an ElementTest with the specified attributes."""
    if attrib is None:
        attrib = {}
    if nsmap is None:
        nsmap = {}
    element = ElementTest(attrib=attrib, nsmap=nsmap)
    element.tag = tag
    element.text = text
    return element


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
