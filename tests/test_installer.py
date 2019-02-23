from pathlib import Path
from unittest.mock import Mock

import pytest
from pyfomod import fomod, installer


def test_installeroption():
    test_option = fomod.Option()
    test_option.name = "name"
    test_option.description = "description"
    test_option.image = "image"
    test_option.type = fomod.OptionType.REQUIRED
    inst_option = installer.InstallerOption(None, test_option)
    assert inst_option._object is test_option
    assert inst_option._installer is None
    assert inst_option.name == "name"
    assert inst_option.description == "description"
    assert inst_option.image == "image"
    assert inst_option.type is fomod.OptionType.REQUIRED
    test_option.type = fomod.Type()
    test_option.type.default = fomod.OptionType.NOTUSABLE
    installer_mock = Mock(spec=installer.Installer)
    inst_option = installer.InstallerOption(installer_mock, test_option)
    assert inst_option._installer is installer_mock
    assert inst_option.type is fomod.OptionType.NOTUSABLE
    test_option.type[fomod.Conditions()] = fomod.OptionType.COULDBEUSABLE
    inst_option = installer.InstallerOption(installer_mock, test_option)
    assert inst_option.type is fomod.OptionType.COULDBEUSABLE


def test_installergroup():
    test_group = fomod.Group()
    test_group.name = "name"
    test_group.type = fomod.GroupType.ALL
    installer_mock = Mock(spec=installer.Installer)
    installer_mock._order_list.return_value = ["test1", "test2", "test3"]
    inst_group = installer.InstallerGroup(installer_mock, test_group)
    assert inst_group.name == "name"
    assert inst_group.type is fomod.GroupType.ALL
    assert list(inst_group) == ["test1", "test2", "test3"]


def test_installerpage():
    test_page = fomod.Page()
    test_page.name = "name"
    installer_mock = Mock(spec=installer.Installer)
    installer_mock._order_list.return_value = ["test1", "test2", "test3"]
    inst_page = installer.InstallerPage(installer_mock, test_page)
    assert inst_page.name == "name"
    assert list(inst_page) == ["test1", "test2", "test3"]


def test_fileinfo_process_files(tmp_path):
    def fileinfo_list_contains(info_list, test_info):
        for fileinfo in info_list:
            if (
                test_info.source == fileinfo.source
                and test_info.destination == fileinfo.destination
                and test_info.priority == fileinfo.priority
            ):
                return True
        return False

    test_files = fomod.Files()
    test_file = fomod.File("file")
    test_file.src = "file1"
    test_file.dst = None
    test_files._file_list.append(test_file)
    test_file = fomod.File("file")
    test_file.src = "file2"
    test_file.dst = ""
    test_files._file_list.append(test_file)
    test_file = fomod.File("file")
    test_file.src = "file3"
    test_file.dst = "dest1/"
    test_files._file_list.append(test_file)
    test_file = fomod.File("file", attrib={"priority": "1"})
    test_file.src = "file4"
    test_file.dst = "dest2"
    test_files._file_list.append(test_file)
    test_file = fomod.File("file")
    test_file.src = "folder1"
    test_file.dst = None
    (tmp_path / "folder1").mkdir()
    (tmp_path / "folder1" / "file11").touch()
    (tmp_path / "folder1" / "folder11").mkdir()
    (tmp_path / "folder1" / "folder12").mkdir()
    (tmp_path / "folder1" / "folder12" / "file12").touch()
    test_files._file_list.append(test_file)
    test_file = fomod.File("file")
    test_file.src = "folder2"
    test_file.dst = ""
    (tmp_path / "folder2").mkdir()
    (tmp_path / "folder2" / "file21").touch()
    (tmp_path / "folder2" / "folder21").mkdir()
    (tmp_path / "folder2" / "folder22").mkdir()
    (tmp_path / "folder2" / "folder22" / "file22").touch()
    test_files._file_list.append(test_file)
    test_file = fomod.File("file")
    test_file.src = "folder3"
    test_file.dst = "dest3/"
    (tmp_path / "folder3").mkdir()
    (tmp_path / "folder3" / "file31").touch()
    (tmp_path / "folder3" / "folder31").mkdir()
    (tmp_path / "folder3" / "folder32").mkdir()
    (tmp_path / "folder3" / "folder32" / "file32").touch()
    test_files._file_list.append(test_file)
    test_file = fomod.File("file", attrib={"priority": "1"})
    test_file.src = "folder4"
    test_file.dst = "dest4"
    (tmp_path / "folder4").mkdir()
    (tmp_path / "folder4" / "file41").touch()
    (tmp_path / "folder4" / "folder41").mkdir()
    (tmp_path / "folder4" / "folder42").mkdir()
    (tmp_path / "folder4" / "folder42" / "file42").touch()
    test_files._file_list.append(test_file)
    test_file = fomod.File("folder")
    test_file.src = "folder6"
    test_file.dst = None
    (tmp_path / "folder6").mkdir()
    (tmp_path / "folder6" / "file61").touch()
    (tmp_path / "folder6" / "folder61").mkdir()
    (tmp_path / "folder6" / "folder62").mkdir()
    (tmp_path / "folder6" / "folder62" / "file62").touch()
    test_files._file_list.append(test_file)
    test_file = fomod.File("folder")
    test_file.src = "folder7"
    test_file.dst = ""
    (tmp_path / "folder7").mkdir()
    (tmp_path / "folder7" / "file71").touch()
    (tmp_path / "folder7" / "folder71").mkdir()
    (tmp_path / "folder7" / "folder72").mkdir()
    (tmp_path / "folder7" / "folder72" / "file72").touch()
    test_files._file_list.append(test_file)
    test_file = fomod.File("folder")
    test_file.src = "folder8"
    test_file.dst = "dest5"
    (tmp_path / "folder8").mkdir()
    (tmp_path / "folder8" / "file81").touch()
    (tmp_path / "folder8" / "folder81").mkdir()
    (tmp_path / "folder8" / "folder82").mkdir()
    (tmp_path / "folder8" / "folder82" / "file82").touch()
    test_files._file_list.append(test_file)
    test_file = fomod.File("folder", attrib={"priority": "1"})
    test_file.src = "folder9"
    test_file.dst = "dest6"
    (tmp_path / "folder9").mkdir()
    (tmp_path / "folder9" / "file91").touch()
    (tmp_path / "folder9" / "folder91").mkdir()
    (tmp_path / "folder9" / "folder92").mkdir()
    (tmp_path / "folder9" / "folder92" / "file92").touch()
    test_files._file_list.append(test_file)
    expected = [
        installer.FileInfo("file1", "file1", 0),
        installer.FileInfo("file2", "file2", 0),
        installer.FileInfo("file3", str(Path("dest1", "file3")), 0),
        installer.FileInfo("file4", "dest2", 1),
        installer.FileInfo("folder1", "folder1", 0),
        installer.FileInfo("folder2", "folder2", 0),
        installer.FileInfo("folder3", str(Path("dest3", "folder3")), 0),
        installer.FileInfo("folder4", "dest4", 1),
        installer.FileInfo("folder6", "folder6", 0),
        installer.FileInfo("folder7", ".", 0),
        installer.FileInfo("folder8", "dest5", 0),
        installer.FileInfo("folder9", "dest6", 1),
    ]
    result = installer.FileInfo.process_files(test_files, None)
    assert len(result) == len(expected)
    for info in result:
        assert fileinfo_list_contains(expected, info)
    expected = [
        installer.FileInfo("file1", "file1", 0),
        installer.FileInfo("file2", "file2", 0),
        installer.FileInfo("file3", str(Path("dest1", "file3")), 0),
        installer.FileInfo("file4", "dest2", 1),
        installer.FileInfo(
            str(Path("folder1", "file11")), str(Path("folder1", "file11")), 0
        ),
        installer.FileInfo(
            str(Path("folder1", "folder11")), str(Path("folder1", "folder11")), 0
        ),
        installer.FileInfo(
            str(Path("folder1", "folder12", "file12")),
            str(Path("folder1", "folder12", "file12")),
            0,
        ),
        installer.FileInfo(
            str(Path("folder2", "file21")), str(Path("folder2", "file21")), 0
        ),
        installer.FileInfo(
            str(Path("folder2", "folder21")), str(Path("folder2", "folder21")), 0
        ),
        installer.FileInfo(
            str(Path("folder2", "folder22", "file22")),
            str(Path("folder2", "folder22", "file22")),
            0,
        ),
        installer.FileInfo(
            str(Path("folder3", "file31")), str(Path("dest3", "folder3", "file31")), 0
        ),
        installer.FileInfo(
            str(Path("folder3", "folder31")),
            str(Path("dest3", "folder3", "folder31")),
            0,
        ),
        installer.FileInfo(
            str(Path("folder3", "folder32", "file32")),
            str(Path("dest3", "folder3", "folder32", "file32")),
            0,
        ),
        installer.FileInfo(
            str(Path("folder4", "file41")), str(Path("dest4", "file41")), 1
        ),
        installer.FileInfo(
            str(Path("folder4", "folder41")), str(Path("dest4", "folder41")), 1
        ),
        installer.FileInfo(
            str(Path("folder4", "folder42", "file42")),
            str(Path("dest4", "folder42", "file42")),
            1,
        ),
        installer.FileInfo(
            str(Path("folder6", "file61")), str(Path("folder6", "file61")), 0
        ),
        installer.FileInfo(
            str(Path("folder6", "folder61")), str(Path("folder6", "folder61")), 0
        ),
        installer.FileInfo(
            str(Path("folder6", "folder62", "file62")),
            str(Path("folder6", "folder62", "file62")),
            0,
        ),
        installer.FileInfo(str(Path("folder7", "file71")), "file71", 0),
        installer.FileInfo(str(Path("folder7", "folder71")), "folder71", 0),
        installer.FileInfo(
            str(Path("folder7", "folder72", "file72")),
            str(Path("folder72", "file72")),
            0,
        ),
        installer.FileInfo(
            str(Path("folder8", "file81")), str(Path("dest5", "file81")), 0
        ),
        installer.FileInfo(
            str(Path("folder8", "folder81")), str(Path("dest5", "folder81")), 0
        ),
        installer.FileInfo(
            str(Path("folder8", "folder82", "file82")),
            str(Path("dest5", "folder82", "file82")),
            0,
        ),
        installer.FileInfo(
            str(Path("folder9", "file91")), str(Path("dest6", "file91")), 1
        ),
        installer.FileInfo(
            str(Path("folder9", "folder91")), str(Path("dest6", "folder91")), 1
        ),
        installer.FileInfo(
            str(Path("folder9", "folder92", "file92")),
            str(Path("dest6", "folder92", "file92")),
            1,
        ),
    ]
    result = installer.FileInfo.process_files(test_files, tmp_path)
    assert len(result) == len(expected)
    for info in result:
        assert fileinfo_list_contains(expected, info)


class TestInstaller(object):
    def test_next(self):
        test_root = fomod.Root()
        test_installer = installer.Installer(test_root)
        assert test_installer.next() is None
        test_root.pages.append(fomod.Page())
        test_group = fomod.Group()
        test_group.append(fomod.Option())
        test_group[0].flags["flag"] = "value"
        test_group.append(fomod.Option())
        test_root.pages[0].append(test_group)
        assert test_installer.next()._object is test_root.pages[0]
        test_group.type = fomod.GroupType.ALL
        with pytest.raises(installer.InvalidSelection):
            test_installer.next()
        test_group.type = fomod.GroupType.ATLEASTONE
        with pytest.raises(installer.InvalidSelection):
            test_installer.next()
        test_group.type = fomod.GroupType.EXACTLYONE
        with pytest.raises(installer.InvalidSelection):
            test_installer.next()
        test_group.type = fomod.GroupType.ATMOSTONE
        with pytest.raises(installer.InvalidSelection):
            test_installer.next(
                [
                    installer.InstallerOption(test_installer, test_group[0]),
                    installer.InstallerOption(test_installer, test_group[1]),
                ]
            )
        test_group[0].type = fomod.OptionType.REQUIRED
        with pytest.raises(installer.InvalidSelection):
            test_installer.next()
        test_group[0].type = fomod.OptionType.NOTUSABLE
        with pytest.raises(installer.InvalidSelection):
            test_installer.next(
                [installer.InstallerOption(test_installer, test_group[0])]
            )
        test_root.pages.append(fomod.Page())
        test_root.pages[1].conditions["flag"] = "other"
        test_root.pages.append(fomod.Page())
        assert test_installer.next()._object is test_root.pages[2]
        assert test_installer.next() is None

    def test_previous(self):
        installer_mock = Mock(spec=installer.Installer)
        test_page = fomod.Page()
        test_option = fomod.Option()
        installer_mock._has_finished = True
        installer_mock._previous_pages = [installer.PageInfo(test_page, [test_option])]
        installer_mock._current_page = None
        result = installer.Installer.previous(installer_mock)
        assert result[0]._object is test_page
        assert result[1] == [test_option]
        assert not installer_mock._has_finished
        assert not installer_mock._previous_pages
        assert installer_mock._current_page is test_page
        installer_mock._previous_pages = []
        assert installer.Installer.previous(installer_mock) is None
        assert installer_mock._current_page is None

    def test_files(self):
        installer_mock = Mock(spec=installer.Installer)
        installer_mock.path = None
        files1 = fomod.Files()
        file1 = fomod.File("file", attrib={"priority": "2"})
        file1.src = "source1"
        file1.dst = "dest1"
        files1._file_list = [file1]
        installer_mock.root = Mock(spec=fomod.Root)
        installer_mock.root.files = files1
        files2 = fomod.Files()
        file2 = fomod.File("file", attrib={"priority": "0"})
        file2.src = "source2"
        file2.dst = "dest1"
        file3 = fomod.File("file", attrib={"priority": "0"})
        file3.src = "source3"
        file3.dst = "dest2"
        files2._file_list = [file2, file3]
        option2 = fomod.Option()
        option2.files = files2
        installer_mock._previous_pages = [
            installer.PageInfo(
                None, [installer.InstallerOption(installer_mock, option2)]
            )
        ]
        files3 = fomod.Files()
        file4 = fomod.File("file", attrib={"priority": "1"})
        file4.src = "source4"
        file4.dst = "dest3"
        files3._file_list = [file4]
        installer_mock.root.file_patterns = {fomod.Conditions(): files3}
        expected = {"source1": "dest1", "source3": "dest2", "source4": "dest3"}
        assert installer.Installer.files(installer_mock) == expected

    def test_flags(self):
        installer_mock = Mock(spec=installer.Installer)
        flags1 = fomod.Flags()
        flags1["flag1"] = "value1"
        flags2 = fomod.Flags()
        flags2["flag2"] = "value2"
        flags3 = fomod.Flags()
        flags3["flag1"] = "value3"
        option1 = fomod.Option()
        option1.flags = flags1
        option2 = fomod.Option()
        option2.flags = flags2
        option3 = fomod.Option()
        option3.flags = flags3
        installer_mock._previous_pages = [
            installer.PageInfo(
                None, [installer.InstallerOption(installer_mock, option1)]
            ),
            installer.PageInfo(
                None,
                [
                    installer.InstallerOption(installer_mock, option2),
                    installer.InstallerOption(installer_mock, option3),
                ],
            ),
        ]
        expected = {"flag1": "value3", "flag2": "value2"}
        assert installer.Installer.flags(installer_mock) == expected

    def test_test_file_condition(self):
        installer_mock = Mock(spec=installer.Installer)
        installer_mock.file_type = None
        installer.Installer._test_file_condition(
            installer_mock, "test_file", fomod.FileType.ACTIVE
        )
        installer_mock.file_type = Mock()
        installer_mock.file_type.return_value = fomod.FileType.MISSING
        installer.Installer._test_file_condition(
            installer_mock, "test_file", fomod.FileType.MISSING
        )
        with pytest.raises(installer._FailedCondition):
            installer.Installer._test_file_condition(
                installer_mock, "test_file", fomod.FileType.INACTIVE
            )

    def test_test_flag_condition(self):
        installer_mock = Mock(spec=installer.Installer)
        installer_mock.flags.return_value = {"flag": "value"}
        installer.Installer._test_flag_condition(installer_mock, "flag", "value")
        with pytest.raises(installer._FailedCondition):
            installer.Installer._test_flag_condition(installer_mock, "flag", "other")
        with pytest.raises(installer._FailedCondition):
            installer.Installer._test_flag_condition(installer_mock, "other", "value")

    def test_test_version_condition(self):
        installer_mock = Mock(spec=installer.Installer)
        installer_mock.game_version = None
        installer.Installer._test_version_condition(installer_mock, "0.1")
        installer_mock.game_version = "1.0"
        installer.Installer._test_version_condition(installer_mock, "0.1")
        with pytest.raises(installer._FailedCondition):
            installer.Installer._test_version_condition(installer_mock, "1.1")

    def test_test_conditions(self):
        installer_mock = Mock(spec=installer.Installer)
        test_conditions = fomod.Conditions()
        test_conditions["file"] = fomod.FileType.MISSING
        test_conditions["flag"] = "value"
        test_conditions[None] = "version"
        test_conditions[fomod.Conditions()] = None
        test_conditions.type = fomod.ConditionType.AND
        installer.Installer._test_conditions(installer_mock, test_conditions)
        installer_mock._test_file_condition.assert_called_once_with(
            "file", fomod.FileType.MISSING
        )
        installer_mock._test_flag_condition.assert_called_once_with("flag", "value")
        installer_mock._test_version_condition.assert_called_once_with("version")
        installer_mock._test_conditions.assert_called_once()
        installer_mock._raise_failed_conditions.assert_not_called()
        installer_mock.reset_mock()
        installer_mock._test_file_condition.side_effect = installer._FailedCondition
        installer.Installer._test_conditions(installer_mock, test_conditions)
        installer_mock._raise_failed_conditions.assert_called_once()
        installer_mock.reset_mock()
        test_conditions.type = fomod.ConditionType.OR
        installer.Installer._test_conditions(installer_mock, test_conditions)
        installer_mock._raise_failed_conditions.assert_not_called()
        installer_mock._test_flag_condition.side_effect = installer._FailedCondition
        installer_mock._test_version_condition.side_effect = installer._FailedCondition
        installer_mock._test_conditions.side_effect = installer._FailedCondition
        installer.Installer._test_conditions(installer_mock, test_conditions)
        installer_mock._raise_failed_conditions.assert_called_once()

    def test_order_list(self):
        mock1 = Mock(spec=["name"])
        mock1.name = "bb"
        mock2 = Mock(spec=["name"])
        mock2.name = "cc"
        mock3 = Mock(spec=["name"])
        mock3.name = "aa"
        test_list = [mock1, mock2, mock3]
        expected = [mock1, mock2, mock3]
        result = installer.Installer._order_list(test_list, fomod.Order.EXPLICIT)
        assert result == expected
        expected = [mock3, mock1, mock2]
        result = installer.Installer._order_list(test_list, fomod.Order.ASCENDING)
        assert result == expected
        expected = [mock2, mock1, mock3]
        result = installer.Installer._order_list(test_list, fomod.Order.DESCENDING)
        assert result == expected
        with pytest.raises(ValueError):
            installer.Installer._order_list(test_list, "not an order")
