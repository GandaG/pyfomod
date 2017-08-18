import os
from distutils.dir_util import copy_tree

import pytest
from pyfomod import io


class Test_get_installer_files:
    def test_empty(self, tmpdir):
        with pytest.raises(IOError):
            # mimic a package that does not contain a fomod folder
            io.get_installer_files(str(tmpdir))

    def test_no_fomod_folder(self, tmpdir):
        # mimic a fake path
        fake_path = os.path.join(str(tmpdir), 'fomod')
        with pytest.raises(IOError):
            io.get_installer_files(fake_path)

    def test_missing_info(self, example_fomod, tmpdir):
        copy_tree(example_fomod, str(tmpdir))
        info_path = os.path.join(str(tmpdir), 'fomod', 'info.xml')
        os.remove(info_path)
        with pytest.raises(IOError):
            io.get_installer_files(str(tmpdir))

    def test_missing_config(self, example_fomod, tmpdir):
        copy_tree(example_fomod, str(tmpdir))
        config_path = os.path.join(str(tmpdir), 'fomod', 'ModuleConfig.xml')
        os.remove(config_path)
        with pytest.raises(IOError):
            io.get_installer_files(str(tmpdir))

    def test_valid(self, example_fomod):
        fomod_path = os.path.join(example_fomod, 'fomod')
        base_files = io.get_installer_files(example_fomod)
        fomod_files = io.get_installer_files(fomod_path)
        assert base_files == fomod_files
