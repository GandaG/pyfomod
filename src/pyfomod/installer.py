# Copyright 2016 Daniel Nunes
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from collections import OrderedDict
from collections.abc import Sequence
from distutils.version import LooseVersion
from pathlib import Path

from . import fomod, parser


class _FailedCondition(Exception):
    pass


class FailedCondition(Exception):
    pass


class InvalidSelection(Exception):
    pass


class InstallerOption(object):
    def __init__(self, installer, option):
        self._installer = installer
        self._object = option
        self.name = option.name
        self.description = option.description
        self.image = option.image
        self.type = option.type
        if isinstance(self.type, fomod.Type):
            for conditions, option_type in self.type.items():
                try:
                    self._installer._test_conditions(conditions)
                except FailedCondition:
                    pass
                else:
                    self.type = option_type
                    break
            else:
                self.type = self.type.default


class InstallerGroup(Sequence):
    def __init__(self, installer, group):
        self._installer = installer
        self._object = group
        self._option_list = installer._order_list(
            [InstallerOption(installer, option) for option in group], group.order
        )
        self.name = group.name
        self.type = group.type

    def __getitem__(self, key):
        return self._option_list[key]

    def __len__(self):
        return len(self._option_list)


class InstallerPage(Sequence):
    def __init__(self, installer, page):
        self._installer = installer
        self._object = page
        self._group_list = installer._order_list(
            [InstallerGroup(installer, group) for group in page], page.order
        )
        self.name = page.name

    def __getitem__(self, key):
        return self._group_list[key]

    def __len__(self):
        return len(self._group_list)


class FileInfo(object):
    def __init__(self, source, destination, priority):
        self.source = source
        self.destination = destination
        self.priority = priority

    @classmethod
    def process_files(cls, files, path):
        result = []
        for file_object in files._file_list:
            source = file_object.src
            if source.endswith(("/", "\\")):
                source = source[:-1]
            # normalize path
            source = str(Path(source))
            destination = file_object.dst
            if destination is None:  # omitted destination
                destination = source
            if file_object._tag == "file" and (
                not destination or destination.endswith(("/", "\\"))
            ):
                # if empty or with a trailing slash then dest refers
                # to a folder. Post-processing to add the filename to the
                # end of the path.
                destination = str(Path(destination) / Path(source).name)
            else:
                # destination still needs normalizing
                destination = str(Path(destination))
            priority = int(file_object._attrib.get("priority", "0"))
            if (
                path is None
                or not (path / source).exists()
                or (path / source).is_file()
            ):
                result.append(cls(source, destination, priority))
                continue
            source_path = path / source
            for dirpath, dirnames, fnames in os.walk(source_path):
                if not dirnames and not fnames:
                    src = str(Path(dirpath).relative_to(path))
                    dst = str(Path(destination, Path(dirpath).relative_to(source_path)))
                    result.append(cls(src, dst, priority))
                    continue
                for fname in fnames:
                    src = str(Path(dirpath, fname).relative_to(path))
                    dst = str(
                        Path(destination, Path(dirpath, fname).relative_to(source_path))
                    )
                    result.append(cls(src, dst, priority))
        return result


class Installer(object):
    def __init__(self, root, path=None, game_version=None, file_type=None):
        self.game_version = game_version
        self.file_type = file_type
        if isinstance(root, fomod.Root):
            self.root = root
        else:
            self.root = parser.parse(root)
            if isinstance(root, (str, Path)) and path is None:
                self.path = root
        if path is not None:
            self.path = Path(path)
        self._current_page = None
        self._previous_pages = OrderedDict()
        self._has_finished = False
        self._test_conditions(self.root.conditions)

    def next(self, selected_options=None):
        if self._has_finished:
            return None
        elif self._current_page is None:
            try:
                self._current_page = self.root.pages[0]
                return InstallerPage(self, self.root.pages[0])
            except IndexError:
                self._current_page = None
                return None
        if selected_options is None:
            selected_options = []
        # get the real options
        real_options = [option._object for option in selected_options]
        # validate options
        for group in self._current_page:
            # validate group type
            selected_num = sum(1 for option in real_options if option in group)
            if group.type is fomod.GroupType.ALL and selected_num != len(group):
                raise InvalidSelection(
                    f"Group {group.name} requires all "
                    f"options to be selected but only "
                    f"{selected_num} were selected."
                )
            elif group.type is fomod.GroupType.EXACTLYONE and selected_num != 1:
                raise InvalidSelection(
                    f"Group {group.name} requires exactly "
                    f"one option to be selected but "
                    f"{selected_num} were selected."
                )
            elif group.type is fomod.GroupType.ATLEASTONE and selected_num < 1:
                raise InvalidSelection(
                    f"Group {group.name} requires at "
                    f"least one option to be selected "
                    f"but {selected_num} were selected."
                )
            elif group.type is fomod.GroupType.ATMOSTONE and selected_num > 1:
                raise InvalidSelection(
                    f"Group {group.name} requires at "
                    f"most one option to be selected "
                    f"but {selected_num} were selected."
                )
            # validate option type
            for option in group:
                inst_option = InstallerOption(self, option)  # resolves option type
                if (
                    inst_option.type is fomod.OptionType.REQUIRED
                    and option not in real_options
                ):
                    raise InvalidSelection(
                        f"Option {option.name} is required but was not selected."
                    )
                elif (
                    inst_option.type is fomod.OptionType.NOTUSABLE
                    and option in real_options
                ):
                    raise InvalidSelection(
                        f"Option {option.name} is not usable but was selected."
                    )
        # sort options
        sorted_list = [option for group in self._current_page for option in group]
        real_options = sorted(real_options, key=sorted_list.index)
        self._previous_pages[self._current_page] = real_options
        # order pages
        ordered_pages = self._order_list(self.root.pages, self.root.pages.order)
        current_index = ordered_pages.index(self._current_page)
        for page in ordered_pages[current_index + 1 :]:
            try:
                self._test_conditions(page.conditions)
            except FailedCondition:
                pass
            else:
                self._current_page = page
                return InstallerPage(self, page)
        else:
            self._has_finished = True
            self._current_page = None
            return None

    def previous(self):
        self._has_finished = False
        try:
            page, options = self._previous_pages.popitem(last=True)
            self._current_page = page
            return InstallerPage(self, page), options
        except KeyError:
            self._current_page = None
            return None

    def files(self):
        required_files = FileInfo.process_files(self.root.files, self.path)
        user_files = [
            file_info
            for options in self._previous_pages.values()
            for option in options
            for file_info in FileInfo.process_files(option.files, self.path)
        ]
        conditional_files = []
        for conditions, files in self.root.file_patterns.items():
            try:
                self._test_conditions(conditions)
            except FailedCondition:
                pass
            else:
                conditional_files.extend(FileInfo.process_files(files, self.path))
        file_dict = {}  # src -> dst
        priority_dict = {}  # dst -> priority
        for info in required_files + user_files + conditional_files:
            if info.destination in priority_dict:
                if priority_dict[info.destination] > info.priority:
                    continue
                del file_dict[info.destination]
            file_dict[info.destination] = info.source
            priority_dict[info.destination] = info.priority
        return {b: a for a, b in file_dict.items()}

    def flags(self):
        flag_dict = {}
        flags_list = [
            option.flags
            for options in self._previous_pages.values()
            for option in options
        ]
        for flags in flags_list:
            for flag, value in flags.items():
                flag_dict[flag] = value
        return flag_dict

    def _test_file_condition(self, file_name, file_type):
        if self.file_type is None:
            return
        actual_type = self.file_type(file_name)
        if actual_type is not file_type:
            raise _FailedCondition(
                f"File {file_name} should be {file_type.value} "
                f"but is {actual_type.value} intead."
            )

    def _test_flag_condition(self, flag_name, flag_value):
        actual_value = self.flags().get(flag_name, None)
        if actual_value != flag_value:
            raise _FailedCondition(
                f"Flag {flag_name} was expected to have "
                f"{flag_value} but has {actual_value} instead."
            )

    def _test_version_condition(self, version):
        if self.game_version is None:
            return
        game_version = LooseVersion(self.game_version)
        version = LooseVersion(version)
        if game_version < version:
            raise _FailedCondition(
                f"Game version is {game_version} but {version} is required."
            )

    @staticmethod
    def _raise_failed_conditions(failed):
        msg = "The following condition(s) have failed:"
        for cond in failed:
            msg += "\n\t" + cond
        raise FailedCondition(msg)

    def _test_conditions(self, conditions):
        op = conditions.type
        failed = []
        for key, value in conditions.items():
            try:
                if key is None:
                    self._test_version_condition(value)
                elif isinstance(key, str):
                    if isinstance(value, fomod.FileType):
                        self._test_file_condition(key, value)
                    if isinstance(value, str):
                        self._test_flag_condition(key, value)
                elif isinstance(key, fomod.Conditions):
                    self._test_conditions(key)
            except (FailedCondition, _FailedCondition) as exc:
                if isinstance(exc, FailedCondition):
                    msgs = [a.strip() for a in str(exc).splitlines()[1:]]
                    failed.extend(msgs)
                else:
                    failed.append(str(exc))
                if op is fomod.ConditionType.AND:
                    self._raise_failed_conditions(failed)
        if op is fomod.ConditionType.OR and len(failed) == len(conditions):
            self._raise_failed_conditions(failed)

    @staticmethod
    def _order_list(unordered_list, order):
        if order is fomod.Order.EXPLICIT:
            return unordered_list
        elif order is fomod.Order.ASCENDING:
            return sorted(unordered_list, key=lambda x: x.name)
        elif order is fomod.Order.DESCENDING:
            return sorted(unordered_list, key=lambda x: x.name, reverse=True)
        else:
            raise ValueError(f"Arguments are incorrect: {unordered_list}, {order}")
