from pyfomod import parser, tree

import mock
import pytest
from helpers import test_parser


class TestRoot():
    def test_info_root(self):
        test_func = tree.Root.info_root.fget

        test_parser.info_root = 'success'

        assert test_func(test_parser.makeelement('a')) == 'success'

    def test_metadata_props(self):
        """
        This tests the metadata properties:
        name, author, version, description, website and image
        """
        info = b"<fomod><Author>author</Author></fomod>"
        conf = b"<config><moduleName/></config>"
        root = parser.from_string(info, conf)

        assert root.name == ''
        root.name = 'name'
        assert root.name == 'name'
        assert root.find('moduleName').text == 'name'

        assert root.author == 'author'
        root.author = 'new author'
        assert root.author == 'new author'
        assert root.info_root.find('Author').text == 'new author'

        assert root.version == ''
        root.version = '1.1'
        assert root.version == '1.1'

        root.description = 'desc'
        assert root.description == 'desc'

        root.website = 'web'
        assert root.website == 'web'

        assert root.image == ''
        root.image = 'path/to/image.png'
        assert root.image == 'path/to/image.png'
        assert root.find('moduleImage').get('path') == 'path/to/image.png'

    def test_xpath_to_message(self):
        test_func = tree.Root._xpath_to_message

        elem_exp = '//element'
        attr_exp = elem_exp + '[@attribute]'
        value_exp = attr_exp[:-1] + '="value"]'

        mock_self = mock.Mock(spec=tree.Root)
        mock_self.soft_incompat = [elem_exp]
        mock_self.hard_incompat = [attr_exp, value_exp]

        base_msg = 'The following {} incompatibilities have been found:'
        soft_msg = base_msg.format('soft')
        hard_msg = base_msg.format('hard')
        msg_elem = 'The element element;'
        msg_attr = 'The attribute attribute in element element;'
        msg_val = 'The value value of attribute attribute in element element;'
        expected_elem = '\n    '.join((soft_msg, msg_elem)) + '\n'
        expected_attr = '\n    '.join((hard_msg, msg_attr, msg_elem))
        expected_val = '\n    '.join((hard_msg, msg_val, msg_attr, msg_elem))

        assert test_func(mock_self, elem_exp) == expected_elem
        assert test_func(mock_self, attr_exp) == expected_attr
        assert test_func(mock_self, value_exp) == expected_val

    def test_is_tree_compatible(self):
        test_func = tree.Root.is_tree_compatible

        root = parser.new()
        assert test_func(root)
        assert test_func(root, True)

        root.find('moduleName').set_attribute('colour', '000000')
        assert test_func(root)
        with pytest.raises(tree.TreeCompatibilityError):
            test_func(root, True)

        root.find('moduleName').set_attribute('colour', None)
        root.add_child('installSteps')
        assert not test_func(root)
        with pytest.raises(tree.TreeCompatibilityError):
            test_func(root, True)

        order_exp = '//installSteps | ' \
                    '//optionalFileGroups | ' \
                    '//plugins'
        for elem in root.xpath(order_exp):
            elem.set_attribute('order', 'Explicit')
        assert test_func(root)
        assert test_func(root, True)
