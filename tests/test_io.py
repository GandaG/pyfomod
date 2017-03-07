import os

import pytest
from pyfomod import io


class Test_get_installer_files:
    def test_empty(self, tmpdir):
        with pytest.raises(IOError):
            # mimic a package that does not contain a fomod folder
            io.get_installer_files(str(tmpdir))

    def test_no_fomod_folder(self, tmpdir):
        with pytest.raises(IOError):
            # mimic a fake path
            fake_path = os.path.join(str(tmpdir), 'fomod')
            io.get_installer_files(fake_path)

    def test_missing_info(self, missing_info_fomod):
        with pytest.raises(IOError):
            io.get_installer_files(missing_info_fomod)

    def test_missing_config(self, missing_config_fomod):
        with pytest.raises(IOError):
            io.get_installer_files(missing_config_fomod)

    def test_valid(self, valid_fomod):
        fomod_path = os.path.join(valid_fomod, 'fomod')
        base_files = io.get_installer_files(valid_fomod)
        fomod_files = io.get_installer_files(fomod_path)
        assert base_files == fomod_files
