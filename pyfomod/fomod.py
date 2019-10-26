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

from collections import OrderedDict
from enum import Enum

from .base import HashableMapping, HashableSequence
from .warnings import (
    AtLeastOneWarning,
    AtMostOneWarning,
    EmptyConditionsWarning,
    EmptyGroupWarning,
    EmptyOptionWarning,
    EmptyPageWarning,
    EmptySourceWarning,
    EmptyTreeWarning,
    EmptyTypeWarning,
    ExactlyOneMissingWarning,
    ExactlyOneRequiredWarning,
    FileDependencyWarning,
    GroupNameWarning,
    ImpossibleFlagWarning,
    InstallerNameWarning,
    MissingDestinationWarning,
    OptionDescriptionWarning,
    OptionNameWarning,
    OrderWarning,
    PageNameWarning,
    UselessFlagsWarning,
    VersionDependencyWarning,
)


class FomodEnum(Enum):
    @classmethod
    def default(cls):
        # default becomes the first defined member
        return list(cls.__members__.values())[0]


class ConditionType(FomodEnum):
    AND = "And"
    OR = "Or"


class FileType(FomodEnum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    MISSING = "Missing"


class Order(FomodEnum):
    ASCENDING = "Ascending"
    DESCENDING = "Descending"
    EXPLICIT = "Explicit"


class GroupType(FomodEnum):
    ANY = "SelectAny"
    ALL = "SelectAll"
    ATLEASTONE = "SelectAtLeastOne"
    ATMOSTONE = "SelectAtMostOne"
    EXACTLYONE = "SelectExactlyOne"


class OptionType(FomodEnum):
    OPTIONAL = "Optional"
    REQUIRED = "Required"
    RECOMMENDED = "Recommended"
    NOTUSABLE = "NotUsable"
    COULDBEUSABLE = "CouldBeUsable"


class BaseFomod(object):
    def __init__(self, tag, attrib):
        self._tag = tag
        self._attrib = attrib
        self._children = OrderedDict()
        self._lineno = None

    @property
    def lineno(self):
        return self._lineno

    def to_string(self):
        raise NotImplementedError()

    def validate(self, **callbacks):
        warnings = []
        for key, funcs in callbacks.items():
            if isinstance(self, globals()[key]):
                for func in funcs:
                    warnings.extend(func(self))
        return warnings

    @staticmethod
    def _write_attributes(attrib):
        result = ""
        for attr, value in attrib.items():
            result += " "
            result += str(attr)
            result += "="
            result += '"{}"'.format(str(value))
        return result

    def _write_children(self):
        children = ""
        for tag, data in self._children.items():
            attribs = data[0]
            text = data[1]
            attribs_str = self._write_attributes(attribs)
            if text:
                children += "\n" + "<{0}{2}>{1}</{0}>".format(tag, text, attribs_str)
            else:
                children += "\n" + "<{}{}/>".format(tag, attribs_str)
        return children


class Root(BaseFomod):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("config", attrib)
        # these attributes are set for max compatibility
        schema_url = "http://qconsulting.ca/fo3/ModConfig5.0.xsd"
        self._attrib = {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": schema_url,
        }
        self._info = Info()
        self._name = Name()
        self._image = Image()
        self._conditions = Conditions()
        self._conditions._tag = "moduleDependencies"
        self._files = Files()
        self._files._tag = "requiredInstallFiles"
        self._pages = Pages()
        self._file_patterns = FilePatterns()

    @property
    def name(self):
        return self._name.name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._name.name = value

    @property
    def image(self):
        return self._image._attrib.get("path", "")

    @image.setter
    def image(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._image._attrib["path"] = value

    @property
    def author(self):
        return self._info.get_text("Author")

    @author.setter
    def author(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._info.set_text("Author", value)

    @property
    def version(self):
        return self._info.get_text("Version")

    @version.setter
    def version(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._info.set_text("Version", value)

    @property
    def description(self):
        return self._info.get_text("Description")

    @description.setter
    def description(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._info.set_text("Description", value)

    @property
    def website(self):
        return self._info.get_text("Website")

    @website.setter
    def website(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._info.set_text("Website", value)

    @property
    def conditions(self):
        return self._conditions

    @conditions.setter
    def conditions(self, value):
        if not isinstance(value, Conditions):
            raise ValueError("Value should be Conditions.")
        self._conditions = value
        self._conditions._tag = "moduleDependencies"

    @property
    def files(self):
        return self._files

    @files.setter
    def files(self, value):
        if not isinstance(value, Files):
            raise ValueError("Value should be Files.")
        self._files = value
        self._files._tag = "requiredInstallFiles"

    @property
    def pages(self):
        return self._pages

    @pages.setter
    def pages(self, value):
        if not isinstance(value, Pages):
            raise ValueError("Value should be Pages.")
        self._pages = value

    @property
    def file_patterns(self):
        return self._file_patterns

    @file_patterns.setter
    def file_patterns(self, value):
        if not isinstance(value, FilePatterns):
            raise ValueError("Value should be FilePatterns.")
        self._file_patterns = value

    def installer(self, path=None, game_version=None, file_type=None):
        from .installer import Installer

        return Installer(self, path, game_version, file_type)

    def to_string(self):
        children = ""
        head = "<{}{}>".format(self._tag, self._write_attributes(self._attrib))
        children += "\n" + self._name.to_string()
        if self._image._attrib:
            children += "\n" + self._image.to_string()
        if self._conditions:
            children += "\n" + self._conditions.to_string()
        if self._files:
            children += "\n" + self._files.to_string()
        if self._pages:
            children += "\n" + self._pages.to_string()
        if self._file_patterns:
            children += "\n" + self._file_patterns.to_string()
        children = children.replace("\n", "\n  ")
        tail = "</{}>".format(self._tag)
        return "{}{}\n{}".format(head, children, tail)

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        flag_set = []
        flag_dep = []

        def parse_conditions(conditions):
            result = []
            for key, value in conditions.items():
                if isinstance(key, Conditions):
                    result.extend(parse_conditions(key))
                elif isinstance(key, str) and isinstance(value, str):
                    result.append((key, conditions))
            return result

        # the lambdas need the 'or []' to comply with returning a list
        callbacks.setdefault("Conditions", []).append(
            lambda x: flag_dep.extend(parse_conditions(x)) or []
        )
        callbacks.setdefault("Flags", []).append(
            lambda x: flag_set.extend(x.keys()) or []
        )
        warnings.extend(self._info.validate(**callbacks))
        warnings.extend(self._name.validate(**callbacks))
        if self._image._attrib:
            warnings.extend(self._image.validate(**callbacks))
        if self._conditions:
            warnings.extend(self._conditions.validate(**callbacks))
        if self._files:
            warnings.extend(self._files.validate(**callbacks))
        if self._pages:
            warnings.extend(self._pages.validate(**callbacks))
        if self._file_patterns:
            warnings.extend(self._file_patterns.validate(**callbacks))
        if not self._files and not self._pages and not self._file_patterns:
            warnings.append(EmptyTreeWarning(self))

        for flag, instance in flag_dep:
            if flag not in flag_set:
                warnings.append(ImpossibleFlagWarning(flag, instance))

        return warnings


class Info(BaseFomod):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("fomod", attrib)

    def get_text(self, tag):
        for key, value in self._children.items():
            if key.lower() == tag.lower():
                return value[1]
        return ""

    def set_text(self, tag, text):
        for key, value in self._children.items():
            if key.lower() == tag.lower():
                self._children[key] = (value[0], text)
                return
        self._children[tag] = ({}, text)

    def to_string(self):
        head = "<{}{}>".format(self._tag, self._write_attributes(self._attrib))
        children = self._write_children()
        children = children.replace("\n", "\n  ")
        tail = "</{}>".format(self._tag)
        return "{}{}\n{}".format(head, children, tail)


class Name(BaseFomod):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("moduleName", attrib)
        self.name = ""

    def to_string(self):
        attrib = self._write_attributes(self._attrib)
        return "<{0}{1}>{2}</{0}>".format(self._tag, attrib, self.name)

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        if not self.name:
            warnings.append(InstallerNameWarning(self))
        return warnings


class Image(BaseFomod):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("moduleImage", attrib)

    def to_string(self):
        attrib = self._write_attributes(self._attrib)
        return "<{0}{1}/>".format(self._tag, attrib)


class Conditions(BaseFomod, HashableMapping):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("dependencies", attrib)
        self._type = ConditionType.AND
        self._map = OrderedDict()

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if not isinstance(value, ConditionType):
            raise ValueError("Value should be ConditionType.")
        self._type = value

    def __getitem__(self, key):
        return self._map[key]

    def __setitem__(self, key, value):
        if key is not None and not isinstance(key, (str, Conditions)):
            raise TypeError("Key must be either None, string or Conditions.")
        if key is None and not isinstance(value, str):
            raise TypeError("Value for None key must be string.")
        if isinstance(key, str) and not isinstance(value, (str, FileType)):
            raise TypeError("Value for string key must be string or FileType.")
        if isinstance(key, Conditions):
            if value is not None:
                raise TypeError("Value for Conditions key must be None.")
            key._tag = "dependencies"
        self._map[key] = value

    def __delitem__(self, key):
        del self._map[key]

    def __iter__(self):
        return iter(self._map)

    def __len__(self):
        return len(self._map)

    def to_string(self):
        children = ""
        attrib = dict(self._attrib)
        attrib["operator"] = self._type.value
        head = "<{}{}>".format(self._tag, self._write_attributes(attrib))
        for key, value in self._map.items():
            if key is None and bool(value):
                child = '<gameDependency version="{}"/>'.format(value)
            elif isinstance(key, Conditions) and bool(key):
                child = key.to_string()
            elif isinstance(value, str):  # string key
                tag = "flagDependency"
                child = '<{} flag="{}" value="{}"/>'.format(tag, key, value)
            elif isinstance(value, FileType) and bool(key):  # string key
                tag = "fileDependency"
                child = '<{} file="{}" state="{}"/>'.format(tag, key, value.value)
            children += "\n" + child
        children = children.replace("\n", "\n  ")
        tail = "</{}>".format(self._tag)
        return "{}{}\n{}".format(head, children, tail)

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        if not self:
            warnings.append(EmptyConditionsWarning(self))
        for key, value in self._map.items():
            if isinstance(key, Conditions):
                warnings.extend(key.validate(**callbacks))
            elif key is None and not value:
                warnings.append(VersionDependencyWarning(self))
            elif isinstance(key, str):
                if not key and isinstance(value, FileType):
                    warnings.append(FileDependencyWarning(self))
                elif self._tag == "moduleDependencies" and isinstance(value, str):
                    warnings.append(UselessFlagsWarning(key, self))
        return warnings


class Files(BaseFomod, HashableMapping):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("files", attrib)
        self._file_list = []

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise TypeError("Key must be string.")
        if key.endswith(("/", "\\")) and key not in self:
            key = key[:-1]
        try:
            return next(a.dst for a in self._file_list if a.src == key)
        except StopIteration:
            raise KeyError()

    # trailing slash -> folder, else file
    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("Key must be string.")
        if not isinstance(value, str):
            raise TypeError("Value must be string.")
        folder = False
        if key.endswith(("/", "\\")) and key not in self:
            key = key[:-1]
            folder = True
        try:
            next(a for a in self._file_list if a.src == key).dst = value
        except StopIteration:
            if folder:
                new = File(tag="folder")
            else:
                new = File(tag="file")
            new.src = key
            new.dst = value
            self._file_list.append(new)

    def __delitem__(self, key):
        if not isinstance(key, str):
            raise TypeError("Key must be string.")
        if key.endswith(("/", "\\")) and key not in self:
            key = key[:-1]
        try:
            value = next(a for a in self._file_list if a.src == key)
            self._file_list.remove(value)
        except StopIteration:
            raise KeyError()

    def __iter__(self):
        for item in self._file_list:
            source = item.src
            if item._tag == "folder" and not source.endswith(("/", "\\")):
                source = "{}/".format(source)
            yield source

    def __len__(self):
        return len(self._file_list)

    def __contains__(self, key):
        try:
            next(a for a in self._file_list if a.src == key)
            return True
        except StopIteration:
            return False

    def to_string(self):
        children = ""
        head = "<{}{}>".format(self._tag, self._write_attributes(self._attrib))
        for child in self._file_list:
            children += "\n" + child.to_string()
        children = children.replace("\n", "\n  ")
        tail = "</{}>".format(self._tag)
        return "{}{}\n{}".format(head, children, tail)

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        for child in self._file_list:
            warnings.extend(child.validate(**callbacks))
        return warnings


class File(BaseFomod):
    def __init__(self, tag="", attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__(tag, attrib)
        self.src = ""
        self.dst = ""

    def to_string(self):
        attrib = dict(self._attrib)
        attrib["source"] = self.src
        if self.dst is not None:
            attrib["destination"] = self.dst
        elif "destination" in attrib:
            del attrib["destination"]
        return "<{}{}/>".format(self._tag, self._write_attributes(attrib))

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        if not self.src:
            warnings.append(EmptySourceWarning(self))
        if self.dst is None:
            warnings.append(MissingDestinationWarning(self))
        return warnings


class Pages(BaseFomod, HashableSequence):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("installSteps", attrib)
        self._page_list = []
        self._order = Order.EXPLICIT

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, value):
        if not isinstance(value, Order):
            raise ValueError("Value should be Order.")
        self._order = value

    def __getitem__(self, key):
        return self._page_list[key]

    def __setitem__(self, key, value):
        if not isinstance(value, Page):
            raise ValueError("Value should be Page.")
        self._page_list[key] = value

    def __delitem__(self, key):
        del self._page_list[key]

    def __len__(self):
        return len(self._page_list)

    def insert(self, key, value):
        if not isinstance(value, Page):
            raise ValueError("Value should be Page.")
        self._page_list.insert(key, value)

    def to_string(self):
        children = ""
        attrib = dict(self._attrib)
        attrib["order"] = self._order.value
        head = "<{}{}>".format(self._tag, self._write_attributes(attrib))
        for child in self._page_list:
            if child:
                children += "\n" + child.to_string()
        children = children.replace("\n", "\n  ")
        tail = "</{}>".format(self._tag)
        return "{}{}\n{}".format(head, children, tail)

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        if self.order is not Order.EXPLICIT:
            warnings.append(OrderWarning(self.order, self))
        for page in self._page_list:
            warnings.extend(page.validate(**callbacks))
        return warnings


class Page(BaseFomod, HashableSequence):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("installStep", attrib)
        self._group_list = []
        self._name = ""
        self._conditions = Conditions()
        self._conditions._tag = "visible"
        self._order = Order.EXPLICIT

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._name = value

    @property
    def conditions(self):
        return self._conditions

    @conditions.setter
    def conditions(self, value):
        if not isinstance(value, Conditions):
            raise ValueError("Value should be Conditions.")
        self._conditions = value
        self._conditions._tag = "visible"

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, value):
        if not isinstance(value, Order):
            raise ValueError("Value should be Order.")
        self._order = value

    def __getitem__(self, key):
        return self._group_list[key]

    def __setitem__(self, key, value):
        if not isinstance(value, Group):
            raise ValueError("Value should be Group.")
        self._group_list[key] = value

    def __delitem__(self, key):
        del self._group_list[key]

    def __len__(self):
        return len(self._group_list)

    def insert(self, key, value):
        if not isinstance(value, Group):
            raise ValueError("Value should be Group.")
        self._group_list.insert(key, value)

    def to_string(self):
        children = ""
        grp_tag = "optionalFileGroups"
        attrib = dict(self._attrib)
        attrib["name"] = self._name
        grp_attrib = {"order": self._order.value}
        head = "<{}{}>".format(self._tag, self._write_attributes(attrib))
        grp_head = "<{}{}>".format(grp_tag, self._write_attributes(grp_attrib))
        grp_tail = "</{}>".format(grp_tag)
        tail = "</{}>".format(self._tag)
        if self._conditions:
            children += "\n" + self._conditions.to_string()
        children += "\n" + grp_head
        for child in self._group_list:
            if child:
                children += "\n  " + child.to_string().replace("\n", "\n  ")
        children += "\n" + grp_tail
        children = children.replace("\n", "\n  ")
        return "{}{}\n{}".format(head, children, tail)

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        if not self:
            warnings.append(EmptyPageWarning(self))
        if not self._name:
            warnings.append(PageNameWarning(self))
        if self.order is not Order.EXPLICIT:
            warnings.append(OrderWarning(self.order, self))
        if self._conditions:
            warnings.extend(self._conditions.validate(**callbacks))
        for group in self._group_list:
            warnings.extend(group.validate(**callbacks))
        return warnings


class Group(BaseFomod, HashableSequence):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("group", attrib)
        self._option_list = []
        self._name = ""
        self._order = Order.EXPLICIT
        self._type = GroupType.ATLEASTONE

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._name = value

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, value):
        if not isinstance(value, Order):
            raise ValueError("Value should be Order.")
        self._order = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if not isinstance(value, GroupType):
            raise ValueError("Value should be GroupType.")
        self._type = value

    def __getitem__(self, key):
        return self._option_list[key]

    def __setitem__(self, key, value):
        if not isinstance(value, Option):
            raise ValueError("Value should be Option.")
        self._option_list[key] = value

    def __delitem__(self, key):
        del self._option_list[key]

    def __len__(self):
        return len(self._option_list)

    def insert(self, key, value):
        if not isinstance(value, Option):
            raise ValueError("Value should be Option.")
        self._option_list.insert(key, value)

    def to_string(self):
        children = ""
        opt_tag = "plugins"
        attrib = dict(self._attrib)
        attrib["name"] = self._name
        attrib["type"] = self._type.value
        opt_attrib = {"order": self._order.value}
        head = "<{}{}>".format(self._tag, self._write_attributes(attrib))
        opt_head = "<{}{}>".format(opt_tag, self._write_attributes(opt_attrib))
        opt_tail = "</{}>".format(opt_tag)
        tail = "</{}>".format(self._tag)
        children += "\n" + opt_head
        for child in self._option_list:
            children += "\n  " + child.to_string().replace("\n", "\n  ")
        children += "\n" + opt_tail
        children = children.replace("\n", "\n  ")
        return "{}{}\n{}".format(head, children, tail)

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        if not self:
            warnings.append(EmptyGroupWarning(self))
        if not self._name:
            warnings.append(GroupNameWarning(self))
        if self.order is not Order.EXPLICIT:
            warnings.append(OrderWarning(self.order, self))

        option_num = len(self._option_list)
        required_options = 0
        notusable_options = 0

        for option in self._option_list:
            warnings.extend(option.validate(**callbacks))
            if isinstance(option.type, OptionType):
                if option.type is OptionType.REQUIRED:
                    required_options += 1
                elif option.type is OptionType.NOTUSABLE:
                    notusable_options += 1
            else:
                if OptionType.REQUIRED in option.type.values():
                    required_options += 1
                elif OptionType.NOTUSABLE in option.type.values():
                    notusable_options += 1

        if notusable_options == option_num:
            if self.type is GroupType.ATLEASTONE:
                warnings.append(AtLeastOneWarning(self))
            elif self.type is GroupType.EXACTLYONE:
                warnings.append(ExactlyOneMissingWarning(self))
        elif required_options >= 2:
            if self.type is GroupType.ATMOSTONE:
                warnings.append(AtMostOneWarning(self))
            elif self.type is GroupType.EXACTLYONE:
                warnings.append(ExactlyOneRequiredWarning(self))
        return warnings


class Option(BaseFomod):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("plugin", attrib)
        self._name = ""
        self._description = ""
        self._image = ""
        self._files = Files()
        self._files._tag = "files"
        self._flags = Flags()
        self._type = OptionType.OPTIONAL

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._description = value

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, value):
        if not isinstance(value, str):
            raise ValueError("Value should be string.")
        self._image = value

    @property
    def files(self):
        return self._files

    @files.setter
    def files(self, value):
        if not isinstance(value, Files):
            raise ValueError("Value should be Files.")
        self._files = value
        self._files._tag = "files"

    @property
    def flags(self):
        return self._flags

    @flags.setter
    def flags(self, value):
        if not isinstance(value, Flags):
            raise ValueError("Value should be Flags.")
        self._flags = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if not isinstance(value, (Type, OptionType)):
            raise ValueError("Value should be OptionType or Type.")
        self._type = value

    def to_string(self):
        children = ""
        attrib = dict(self._attrib)
        attrib["name"] = self.name
        head = "<{}{}>".format(self._tag, self._write_attributes(attrib))
        children += "\n"
        children += "<description>{}</description>".format(self.description)
        if self.image:
            children += "\n" + '<image path="{}"/>'.format(self.image)
        if self.files:
            children += "\n" + self.files.to_string()
        if self.flags:
            children += "\n" + self.flags.to_string()
        children += "\n" + "<typeDescriptor>"
        if isinstance(self.type, OptionType):
            children += "\n  " + '<type name="{}"/>'.format(self.type.value)
        else:
            children += "\n  " + self.type.to_string()
        children += "\n" + "</typeDescriptor>"
        children = children.replace("\n", "\n  ")
        tail = "</{}>".format(self._tag)
        return "{}{}\n{}".format(head, children, tail)

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        if not self.name:
            warnings.append(OptionNameWarning(self))
        if not self.description:
            warnings.append(OptionDescriptionWarning(self))
        if not self.files and not self.flags:
            warnings.append(EmptyOptionWarning(self))
        if self.files:
            warnings.extend(self.files.validate(**callbacks))
        if self.flags:
            warnings.extend(self.flags.validate(**callbacks))
        if isinstance(self.type, Type):
            warnings.extend(self.type.validate(**callbacks))
        return warnings


class Flags(BaseFomod, HashableMapping):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("conditionFlags", attrib)
        self._map = OrderedDict()

    def __getitem__(self, key):
        return self._map[key]

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("Key must be string.")
        if not isinstance(value, str):
            raise TypeError("Value must be string.")
        self._map[key] = value

    def __delitem__(self, key):
        del self._map[key]

    def __iter__(self):
        return iter(self._map)

    def __len__(self):
        return len(self._map)

    def to_string(self):
        children = ""
        head = "<{}{}>".format(self._tag, self._write_attributes(self._attrib))
        for key, value in self._map.items():
            children += "\n" + '<flag name="{}">{}</flag>'.format(key, value)
        children = children.replace("\n", "\n  ")
        tail = "</{}>".format(self._tag)
        return "{}{}\n{}".format(head, children, tail)


class Type(BaseFomod, HashableMapping):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("dependencyType", attrib)
        self._default = OptionType.OPTIONAL
        self._map = OrderedDict()

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, value):
        if not isinstance(value, OptionType):
            raise ValueError("Value should be OptionType.")
        self._default = value

    def __getitem__(self, key):
        return self._map[key]

    def __setitem__(self, key, value):
        if not isinstance(key, Conditions):
            raise TypeError("Key must be Conditions.")
        if not isinstance(value, OptionType):
            raise TypeError("Value must be OptionType.")
        key._tag = "dependencies"
        self._map[key] = value

    def __delitem__(self, key):
        del self._map[key]

    def __iter__(self):
        return iter(self._map)

    def __len__(self):
        return len(self._map)

    def to_string(self):
        children = ""
        head = "<{}{}>".format(self._tag, self._write_attributes(self._attrib))
        children += "\n"
        children += '<defaultType name="{}"/>'.format(self.default.value)
        children += "\n" + "<patterns>"
        for key, value in self._map.items():
            children += "\n  " + "<pattern>"
            children += "\n    " + key.to_string().replace("\n", "\n    ")
            children += "\n    " + '<type name="{}"/>'.format(value.value)
            children += "\n  " + "</pattern>"
        children += "\n" + "</patterns>"
        children = children.replace("\n", "\n  ")
        tail = "</{}>".format(self._tag)
        return "{}{}\n{}".format(head, children, tail)

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        if not self:
            warnings.append(EmptyTypeWarning(self))
        for key in self._map:
            warnings.extend(key.validate(**callbacks))
        return warnings


class FilePatterns(BaseFomod, HashableMapping):
    def __init__(self, attrib=None):
        if attrib is None:
            attrib = {}
        super().__init__("conditionalFileInstalls", attrib)
        self._map = OrderedDict()

    def __getitem__(self, key):
        return self._map[key]

    def __setitem__(self, key, value):
        if not isinstance(key, Conditions):
            raise TypeError("Key must be Conditions.")
        if not isinstance(value, Files):
            raise TypeError("Value must be Files.")
        key._tag = "dependencies"
        value._tag = "files"
        self._map[key] = value

    def __delitem__(self, key):
        del self._map[key]

    def __iter__(self):
        return iter(self._map)

    def __len__(self):
        return len(self._map)

    def to_string(self):
        children = ""
        head = "<{}{}>".format(self._tag, self._write_attributes(self._attrib))
        children += "\n" + "<patterns>"
        for key, value in self._map.items():
            children += "\n  " + "<pattern>"
            children += "\n    " + key.to_string().replace("\n", "\n    ")
            children += "\n    " + value.to_string().replace("\n", "\n    ")
            children += "\n  " + "</pattern>"
        children += "\n" + "</patterns>"
        children = children.replace("\n", "\n  ")
        tail = "</{}>".format(self._tag)
        return "{}{}\n{}".format(head, children, tail)

    def validate(self, **callbacks):
        warnings = super().validate(**callbacks)
        for key, value in self._map.items():
            warnings.extend(key.validate(**callbacks))
            warnings.extend(value.validate(**callbacks))
        return warnings
