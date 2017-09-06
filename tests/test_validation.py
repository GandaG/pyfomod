import os

from lxml import etree

import pytest
from pyfomod import parser, validation


class Test_Validate_Installer:
    def test_root(self):
        root = parser.FOMOD_PARSER.makeelement('config')
        with pytest.raises(NotImplementedError):
            validation.validate_installer(root)

    def test_tuple(self, simple_parse):
        assert validation.validate_installer(tuple(simple_parse))
        simple_parse = (etree.ElementTree(simple_parse[0]),
                        etree.ElementTree(simple_parse[1]))
        assert validation.validate_installer(tuple(simple_parse))

    def test_list(self, simple_parse):
        assert validation.validate_installer(list(simple_parse))
        simple_parse = (etree.ElementTree(simple_parse[0]),
                        etree.ElementTree(simple_parse[1]))
        assert validation.validate_installer(list(simple_parse))

    def test_path(self, example_fomod):
        assert validation.validate_installer(example_fomod)
        assert validation.validate_installer(os.path.join(example_fomod,
                                                          'fomod'))

    def test_invalid_arg(self, tmpdir):
        with pytest.raises(ValueError):
            validation.validate_installer(str(tmpdir))


class Test_Check_Errors:
    def test_root(self):
        root = parser.FOMOD_PARSER.makeelement('config')
        with pytest.raises(NotImplementedError):
            validation.check_for_errors(root)

    def test_tuple(self, simple_parse):
        assert not validation.check_for_errors(tuple(simple_parse))
        simple_parse = (etree.ElementTree(simple_parse[0]),
                        etree.ElementTree(simple_parse[1]))
        assert not validation.check_for_errors(tuple(simple_parse))

    def test_list(self, simple_parse):
        assert not validation.check_for_errors(list(simple_parse))
        simple_parse = (etree.ElementTree(simple_parse[0]),
                        etree.ElementTree(simple_parse[1]))
        assert not validation.check_for_errors(list(simple_parse))

    def test_path(self, example_fomod):
        assert not validation.check_for_errors(example_fomod)
        assert not validation.check_for_errors(os.path.join(example_fomod,
                                                            'fomod'))

    def test_invalid_arg(self, tmpdir):
        with pytest.raises(ValueError):
            validation.check_for_errors(str(tmpdir))

    def test_empty_inst(self):
        package_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'test_validation_empty')
        expected = [(2, "Empty Installer",
                     "The installer is empty.", 'config')]
        assert validation.check_for_errors(package_path) == expected

    def test_empty_source(self):
        package_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'test_validation_emptysource')
        expected = [(5, "Empty Source Fields",
                     "The source folder(s) under the tag file were empty.",
                     'file')]
        assert validation.check_for_errors(package_path) == expected

    def test_missing_folder(self):
        package_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'test_validation_missfolder')
        expected = [(5, "Missing Source Folders",
                     "The source folder(s) under the tag folder "
                     "weren't found inside the package.",
                     'folder')]
        assert validation.check_for_errors(package_path) == expected

    def test_missing_file(self):
        package_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'test_validation_missfile')
        expected = [(5, "Missing Source Files",
                     "The source file(s) under the tag file "
                     "weren't found inside the package.",
                     'file')]
        assert validation.check_for_errors(package_path) == expected

    def test_missing_image(self):
        package_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'test_validation_missimage')
        expected = [(2, "Empty Installer",
                     "The installer is empty.", 'config'),
                    (4, "Missing Images",
                     "The image(s) under the tag moduleImage "
                     "weren't found inside the package.",
                     'moduleImage')]
        assert validation.check_for_errors(package_path) == expected

    def test_flag_label_mismatch(self):
        package_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'test_validation_flaglabel')
        expected = [(5, "Mismatched Flag Labels",
                     "The flag label that flagDependency is dependent on "
                     "is never created during installation.",
                     'flagDependency'),
                    (5, "Mismatched Flag Values",
                     "The flag value that flagDependency is dependent on "
                     "is never set.",
                     'flagDependency')]
        assert validation.check_for_errors(package_path) == expected

    def test_flag_value_mismatch(self):
        package_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'test_validation_flaglabel')
        expected = [(5, "Mismatched Flag Labels",
                     "The flag label that flagDependency is dependent on "
                     "is never created during installation.",
                     'flagDependency'),
                    (5, "Mismatched Flag Values",
                     "The flag value that flagDependency is dependent on "
                     "is never set.",
                     'flagDependency')]
        assert validation.check_for_errors(package_path) == expected
