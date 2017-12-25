import os

from pyfomod import io

import pytest


class Test_get_installer_files:
    def test_empty(self, tmpdir):
        with pytest.raises(FileNotFoundError):
            # mimic a package that does not contain a fomod folder
            io.get_installer_files(str(tmpdir))

    def test_no_fomod_folder(self, tmpdir):
        # mimic a fake path
        fake_path = os.path.join(str(tmpdir), 'fomod')
        with pytest.raises(FileNotFoundError):
            io.get_installer_files(fake_path)

    def test_missing_info(self, tmpdir):
        tmpdir = str(tmpdir)
        os.makedirs(os.path.join(tmpdir, 'fomod'))
        open(os.path.join(tmpdir, 'fomod', 'info.xml'), 'a').close()
        with pytest.raises(FileNotFoundError):
            io.get_installer_files(tmpdir)

    def test_missing_config(self, tmpdir):
        tmpdir = str(tmpdir)
        os.makedirs(os.path.join(tmpdir, 'fomod'))
        open(os.path.join(tmpdir, 'fomod', 'ModuleConfig.xml'), 'a').close()
        with pytest.raises(FileNotFoundError):
            io.get_installer_files(tmpdir)

    def test_valid(self, tmpdir):
        tmpdir = str(tmpdir)
        fomod_path = os.path.join(tmpdir, 'fomod')
        info_file = os.path.join(fomod_path, 'info.xml')
        conf_file = os.path.join(fomod_path, 'ModuleConfig.xml')
        os.makedirs(fomod_path)
        open(info_file, 'a').close()
        open(conf_file, 'a').close()
        assert io.get_installer_files(tmpdir) == (info_file, conf_file)
        assert io.get_installer_files(fomod_path) == (info_file, conf_file)

    def test_create_missing(self, tmpdir):
        tmpdir = str(tmpdir)
        fomod_path = os.path.join(tmpdir, 'fomod')
        info_file = os.path.join(fomod_path, 'info.xml')
        conf_file = os.path.join(fomod_path, 'ModuleConfig.xml')
        assert io.get_installer_files(tmpdir, True) == (info_file, conf_file)
        assert os.path.isdir(fomod_path)
        assert io.get_installer_files(fomod_path, True) == (info_file,
                                                            conf_file)
