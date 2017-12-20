import os

from lxml import etree

import mock
from pyfomod import validation


class Test_Assert_Valid:
    @mock.patch('pyfomod.validation.FOMOD_SCHEMA')
    @mock.patch('pyfomod.validation.etree.parse')
    def test_path(self, mock_parse, mock_schema):
        mock_valid = mock_schema.assert_ = mock.Mock()
        mock_path = mock.Mock(spec=str)
        validation.assert_valid(mock_path)
        mock_parse.assert_called_once_with(mock_path)
        mock_valid.assert_called_once_with(mock_parse.return_value)

    @mock.patch('pyfomod.validation.FOMOD_SCHEMA')
    def test_tree(self, mock_schema):
        mock_valid = mock_schema.assert_ = mock.Mock()
        mock_tree = mock.Mock(spec=etree._Element)
        validation.assert_valid(mock_tree)
        mock_valid.assert_called_once_with(mock_tree)

    @mock.patch('pyfomod.validation.etree.XMLSchema')
    def test_custom_schema(self, mock_schema):
        mock_custom_schema = mock.Mock()
        mock_valid = mock_schema.return_value.assert_ = mock.Mock()
        mock_tree = mock.Mock(spec=etree._Element)
        validation.assert_valid(mock_tree, mock_custom_schema)
        mock_schema.assert_called_once_with(mock_custom_schema)
        mock_valid.assert_called_once_with(mock_tree)


class Test_Validate:
    @mock.patch('pyfomod.validation.FOMOD_SCHEMA')
    @mock.patch('pyfomod.validation.etree.parse')
    def test_path(self, mock_parse, mock_schema):
        mock_valid = mock_schema.validate
        mock_path = mock.Mock(spec=str)
        validation.validate(mock_path)
        mock_parse.assert_called_once_with(mock_path)
        mock_valid.assert_called_once_with(mock_parse.return_value)

    @mock.patch('pyfomod.validation.FOMOD_SCHEMA')
    def test_tree(self, mock_schema):
        mock_valid = mock_schema.validate
        mock_tree = mock.Mock(spec=etree._Element)
        validation.validate(mock_tree)
        mock_valid.assert_called_once_with(mock_tree)

    @mock.patch('pyfomod.validation.etree.XMLSchema')
    def test_custom_schema(self, mock_schema):
        mock_custom_schema = mock.Mock()
        mock_valid = mock_schema.return_value.validate = mock.Mock()
        mock_tree = mock.Mock(spec=etree._Element)
        validation.validate(mock_tree, mock_custom_schema)
        mock_schema.assert_called_once_with(mock_custom_schema)
        mock_valid.assert_called_once_with(mock_tree)


class Test_Check_Errors:
    def test_normal(self, tmpdir):
        tree = etree.fromstring("<fomod>"
                                "<Name>Example Name</Name>"
                                "<Author>Example Author</Author>"
                                "<Version>0</Version>"
                                "<Website>www.example.com</Website>"
                                "</fomod>")
        assert validation.check_for_errors(tree) == []
        tree = etree.ElementTree(tree)
        assert validation.check_for_errors(tree) == []
        path = os.path.join(str(tmpdir), 'fomod.xml')
        tree.write(path)
        assert validation.check_for_errors(path) == []

    def test_no_name(self):
        tree = etree.fromstring("<fomod>"
                                "<Author>Example Author</Author>"
                                "<Version>0</Version>"
                                "<Website>www.example.com</Website>"
                                "</fomod>")
        expected = [([1], "Installer With No Name",
                     "The installer has no name specified.")]
        assert validation.check_for_errors(tree) == expected

    def test_no_author(self):
        tree = etree.fromstring("<fomod>"
                                "<Name>Example Name</Name>"
                                "<Version>0</Version>"
                                "<Website>www.example.com</Website>"
                                "</fomod>")
        expected = [([1], "Unsigned Installer",
                     "The installer has no author specified.")]
        assert validation.check_for_errors(tree) == expected

    def test_no_version(self):
        tree = etree.fromstring("<fomod>"
                                "<Name>Example Name</Name>"
                                "<Author>Example Author</Author>"
                                "<Website>www.example.com</Website>"
                                "</fomod>")
        expected = [([1], "Versionless Installer",
                     "The installer has no version specified.")]
        assert validation.check_for_errors(tree) == expected

    def test_no_website(self):
        tree = etree.fromstring("<fomod>"
                                "<Name>Example Name</Name>"
                                "<Author>Example Author</Author>"
                                "<Version>0</Version>"
                                "</fomod>")
        expected = [([1], "Offline Installer",
                     "The installer has no website specified.")]
        assert validation.check_for_errors(tree) == expected

    def test_empty_inst(self):
        tree = etree.fromstring("<config>"
                                "<moduleName>"
                                "Empty Installer Error"
                                "</moduleName>"
                                "</config>")
        expected = [([1], "Empty Installer",
                     "The installer is empty.")]
        assert validation.check_for_errors(tree) == expected

    def test_empty_source(self):
        tree = etree.fromstring("<config>"
                                "<moduleName>Empty Source Error</moduleName>"
                                "<requiredInstallFiles>"
                                "<file source=''/>"
                                "</requiredInstallFiles>"
                                "</config>")
        expected = [([1], "Empty Source Fields",
                     "The source folder(s) under the tag file were empty.")]
        assert validation.check_for_errors(tree) == expected

    def test_unused_files(self, tmpdir):
        tree = etree.fromstring("<config>"
                                "<moduleName/>"
                                "<moduleImage path='modimg.png'/>"
                                "<requiredInstallFiles>"
                                "<folder source='aa/bb'/>"
                                "<folder source='dd'/>"
                                "<file source='datafile'/>"
                                "<file source='aa/cc/ff.txt'/>"
                                "</requiredInstallFiles>"
                                "<installSteps>"
                                "<installStep name=''>"
                                "<optionalFileGroups>"
                                "<group name='' type='SelectAtLeastOne'>"
                                "<plugins>"
                                "<plugin name=''>"
                                "<description/>"
                                "<image path='img.png'/>"
                                "<conditionFlags>"
                                "<flag name='flag'>value</flag>"
                                "</conditionFlags>"
                                "<typeDescriptor>"
                                "<type name='Optional'/>"
                                "</typeDescriptor>"
                                "</plugin>"
                                "</plugins>"
                                "</group>"
                                "</optionalFileGroups>"
                                "</installStep>"
                                "</installSteps>"
                                "</config>")
        tmpdir = str(tmpdir)
        os.mkdir(os.path.join(tmpdir, 'aa'))
        os.mkdir(os.path.join(tmpdir, 'aa', 'bb'))
        os.mkdir(os.path.join(tmpdir, 'aa', 'cc'))
        os.mkdir(os.path.join(tmpdir, 'dd'))
        gg = os.path.join(tmpdir, 'aa', 'cc', 'gg.txt')
        hh = os.path.join(tmpdir, 'aa', 'hh.txt')
        unuseddatafile = os.path.join(tmpdir, 'unuseddatafile')
        open(os.path.join(tmpdir, 'aa', 'bb', 'ee.txt'), 'a').close()
        open(os.path.join(tmpdir, 'aa', 'cc', 'ff.txt'), 'a').close()
        open(gg, 'a').close()
        open(hh, 'a').close()
        open(os.path.join(tmpdir, 'dd', 'ii.txt'), 'a').close()
        open(os.path.join(tmpdir, 'datafile'), 'a').close()
        open(unuseddatafile, 'a').close()
        open(os.path.join(tmpdir, 'modimg.png'), 'a').close()
        open(os.path.join(tmpdir, 'img.png'), 'a').close()
        gg = "\n    " + os.path.relpath(gg, tmpdir)
        hh = "\n    " + os.path.relpath(hh, tmpdir)
        unuseddatafile = "\n    " + os.path.relpath(unuseddatafile, tmpdir)
        expected = [([1], "Unused Files",
                     "The following file(s) are included within the package"
                     " but are not used:" + unuseddatafile + hh + gg)]
        assert validation.check_for_errors(tree, path=tmpdir) == expected

    def test_missing_folder(self, tmpdir):
        tree = etree.fromstring("<config>"
                                "<moduleName>Empty Source Error</moduleName>"
                                "<requiredInstallFiles>"
                                "<folder source='missing'/>"
                                "</requiredInstallFiles>"
                                "</config>")
        expected = [([1], "Missing Source Folders",
                     "The source folder(s) under the tag folder "
                     "weren't found inside the package.")]
        assert validation.check_for_errors(tree, path=str(tmpdir)) == expected

    def test_missing_file(self, tmpdir):
        tree = etree.fromstring("<config>"
                                "<moduleName>Empty Source Error</moduleName>"
                                "<requiredInstallFiles>"
                                "<file source='missing.txt'/>"
                                "</requiredInstallFiles>"
                                "</config>")
        expected = [([1], "Missing Source Files",
                     "The source file(s) under the tag file "
                     "weren't found inside the package.")]
        assert validation.check_for_errors(tree, path=str(tmpdir)) == expected

    def test_missing_image(self, tmpdir):
        tree = etree.fromstring("<config>"
                                "<moduleName>Empty Source Error</moduleName>"
                                "<moduleImage path='missing.png'/>"
                                "<requiredInstallFiles/>"
                                "</config>")
        expected = [([1], "Missing Images",
                     "The image(s) under the tag moduleImage "
                     "weren't found inside the package.")]
        assert validation.check_for_errors(tree, path=str(tmpdir)) == expected

    def test_flag_label_mismatch(self):
        tree = etree.fromstring("<config>"
                                "<moduleName/>"
                                "<moduleDependencies operator='And'>"
                                "<flagDependency "
                                "flag='Missing Flag' value='Missing'/>"
                                "</moduleDependencies>"
                                "<installSteps>"
                                "<installStep name=''>"
                                "<optionalFileGroups>"
                                "<group name='' type='SelectAtLeastOne'>"
                                "<plugins>"
                                "<plugin name=''>"
                                "<description/>"
                                "<conditionFlags>"
                                "<flag name='flag'>value</flag>"
                                "</conditionFlags>"
                                "<typeDescriptor>"
                                "<type name='Optional'/>"
                                "</typeDescriptor>"
                                "</plugin>"
                                "</plugins>"
                                "</group>"
                                "</optionalFileGroups>"
                                "</installStep>"
                                "</installSteps>"
                                "</config>")
        expected = [([1], "Mismatched Flag Labels",
                     "The flag label that flagDependency is dependent on "
                     "is never created during installation.")]
        assert validation.check_for_errors(tree) == expected

    def test_flag_value_mismatch(self):
        tree = etree.fromstring("<config>"
                                "<moduleName/>"
                                "<moduleDependencies operator='And'>"
                                "<flagDependency "
                                "flag='flag1' value='value'/>"
                                "<flagDependency "
                                "flag='flag2' value='Missing'/>"
                                "</moduleDependencies>"
                                "<installSteps>"
                                "<installStep name=''>"
                                "<optionalFileGroups>"
                                "<group name='' type='SelectAtLeastOne'>"
                                "<plugins>"
                                "<plugin name=''>"
                                "<description/>"
                                "<conditionFlags>"
                                "<flag name='flag1'>value</flag>"
                                "<flag name='flag2'>value</flag>"
                                "</conditionFlags>"
                                "<typeDescriptor>"
                                "<type name='Optional'/>"
                                "</typeDescriptor>"
                                "</plugin>"
                                "</plugins>"
                                "</group>"
                                "</optionalFileGroups>"
                                "</installStep>"
                                "</installSteps>"
                                "</config>")
        expected = [([1], "Mismatched Flag Values",
                     "The flag value that flagDependency is dependent on "
                     "is never set.")]
        assert validation.check_for_errors(tree) == expected
