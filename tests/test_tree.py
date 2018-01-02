from pyfomod import parser, tree

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
