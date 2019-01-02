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

"""Base classes for pyfomod."""

import warnings
from collections import OrderedDict
from collections.abc import ItemsView, KeysView, Mapping, ValuesView
from enum import Enum


class ValidationWarning(UserWarning):
    def __init__(self, title, msg, elem, *args, **kwargs):
        self.title = title
        self.msg = msg
        self.elem = elem
        super().__init__("{} - {}".format(title, msg), *args, **kwargs)


class CriticalWarning(ValidationWarning):
    pass


def warn(title, msg, elem, critical=False):
    if critical:
        warning = CriticalWarning(title, msg, elem)
    else:
        warning = ValidationWarning(title, msg, elem)
    warnings.warn(warning, stacklevel=2)


class ConditionType(Enum):
    AND = "And"
    OR = "Or"


class FileType(Enum):
    MISSING = "Missing"
    INACTIVE = "Inactive"
    ACTIVE = "Active"


class Order(Enum):
    ASCENDING = "Ascending"
    DESCENDING = "Descending"
    EXPLICIT = "Explicit"


class GroupType(Enum):
    ATLEASTONE = "SelectAtLeastOne"
    ATMOSTONE = "SelectAtMostOne"
    EXACTLYONE = "SelectExactlyOne"
    ALL = "SelectAll"
    ANY = "SelectAny"


class OptionType(Enum):
    REQUIRED = "Required"
    OPTIONAL = "Optional"
    RECOMMENDED = "Recommended"
    NOTUSABLE = "NotUsable"
    COULDBEUSABLE = "CouldBeUsable"


class HashableSequence(object):
    def __getitem__(self, key):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __delitem__(self, key):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def insert(self, index, value):
        raise NotImplementedError

    def __iter__(self):
        i = 0
        try:
            while True:
                v = self[i]
                yield v
                i += 1
        except IndexError:
            return

    def __contains__(self, value):
        for v in self:
            if v is value or v == value:
                return True
        return False

    def __reversed__(self):
        for i in reversed(range(len(self))):
            yield self[i]

    def index(self, value, start=0, stop=None):
        if start is not None and start < 0:
            start = max(len(self) + start, 0)
        if stop is not None and stop < 0:
            stop += len(self)

        i = start
        while stop is None or i < stop:
            try:
                v = self[i]
                if v is value or v == value:
                    return i
            except IndexError:
                break
            i += 1
        raise ValueError

    def count(self, value):
        return sum(1 for v in self if v is value or v == value)

    def append(self, value):
        self.insert(len(self), value)

    def clear(self):
        try:
            while True:
                self.pop()
        except IndexError:
            pass

    def reverse(self):
        n = len(self)
        for i in range(n // 2):
            self[i], self[n - i - 1] = self[n - i - 1], self[i]

    def extend(self, values):
        if values is self:
            values = list(values)
        for v in values:
            self.append(v)

    def pop(self, index=-1):
        v = self[index]
        del self[index]
        return v

    def remove(self, value):
        del self[self.index(value)]

    def __iadd__(self, values):
        self.extend(values)
        return self


class HashableMapping(object):
    def __getitem__(self, key):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __delitem__(self, key):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def keys(self):
        return KeysView(self)

    def items(self):
        return ItemsView(self)

    def values(self):
        return ValuesView(self)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    __marker = object()

    def pop(self, key, default=__marker):
        try:
            value = self[key]
        except KeyError:
            if default is self.__marker:
                raise
            return default
        else:
            del self[key]
            return value

    def popitem(self):
        try:
            key = next(iter(self))
        except StopIteration:
            raise KeyError from None
        value = self[key]
        del self[key]
        return key, value

    def clear(self):
        try:
            while True:
                self.popitem()
        except KeyError:
            pass

    def update(*args, **kwargs):
        if not args:
            raise TypeError(
                "descriptor 'update' of 'HashableMapping' object needs an argument"
            )
        self, *args = args
        if len(args) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(args))
        if args:
            other = args[0]
            if isinstance(other, Mapping):
                for key in other:
                    self[key] = other[key]
            elif hasattr(other, "keys"):
                for key in other.keys():
                    self[key] = other[key]
            else:
                for key, value in other:
                    self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default


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
        for key, funcs in callbacks.items():
            if isinstance(self, globals()[key]):
                for func in funcs:
                    func(self)

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

    def to_string(self):
        children = ""
        head = "<{}{}>".format(self._tag, self._write_attributes(self._attrib))
        children += "\n" + self._name.to_string()
        children += self._write_children()  # moduleImage
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
        super().validate(**callbacks)
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

        callbacks.setdefault("Conditions", []).append(
            lambda x: flag_dep.extend(parse_conditions(x))
        )
        callbacks.setdefault("Flags", []).append(lambda x: flag_set.extend(x.keys()))
        self._name.validate(**callbacks)
        if self._conditions:
            self._conditions.validate(**callbacks)
        if self._files:
            self._files.validate(**callbacks)
        if self._pages:
            self._pages.validate(**callbacks)
        if self._file_patterns:
            self._file_patterns.validate(**callbacks)
        if not self._files and not self._pages and not self._file_patterns:
            title = "Empty Installer"
            msg = "This fomod is empty, nothing will be installed."
            warn(title, msg, self)

        for flag, instance in flag_dep:
            if flag not in flag_set:
                title = "Impossible Flags"
                msg = 'The flag "{}" is never created or set.'.format(flag)
                warn(title, msg, instance)


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
        super().validate(**callbacks)
        if not self.name:
            title = "Missing Installer Name"
            msg = "This fomod does not have a name."
            warn(title, msg, self)


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
            if key is None:
                child = '<gameDependency version="{}"/>'.format(value)
            elif isinstance(key, Conditions):
                if not key:
                    continue
                child = key.to_string()
            elif isinstance(value, str):  # string key
                tag = "flagDependency"
                child = '<{} flag="{}" value="{}"/>'.format(tag, key, value)
            elif isinstance(value, FileType):  # string key
                tag = "fileDependency"
                child = '<{} file="{}" state="{}"/>'.format(tag, key, value.value)
            children += "\n" + child
        children = children.replace("\n", "\n  ")
        tail = "</{}>".format(self._tag)
        return "{}{}\n{}".format(head, children, tail)

    def validate(self, **callbacks):
        super().validate(**callbacks)
        if not self:
            title = "Empty Conditions"
            msg = "This element should have at least one condition present."
            warn(title, msg, self, critical=True)
        for key, value in self._map.items():
            if isinstance(key, Conditions):
                if not key:
                    title = "Empty Conditions"
                    msg = (
                        "This element is empty and will not be written to "
                        "prevent errors."
                    )
                    warn(title, msg, key)
                else:
                    key.validate(**callbacks)
            elif key is None and not value:
                title = "Empty Version Dependency"
                msg = "This version dependency is empty " "and may not work correctly."
                warn(title, msg, self)
            elif isinstance(key, str):
                if not key and isinstance(value, FileType):
                    title = "Empty File Dependency"
                    msg = (
                        "This file dependency depends on no file, "
                        "may not work correctly."
                    )
                    warn(title, msg, self)
                elif self._tag == "moduleDependencies" and isinstance(value, str):
                    title = "Useless Flags"
                    msg = (
                        "Flag {} shouldn't be used here "
                        "since it can't have been set.".format(key)
                    )
                    warn(title, msg, self)


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
        super().validate(**callbacks)
        for child in self._file_list:
            child.validate(**callbacks)


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
        if self.dst:
            attrib["destination"] = self.dst
        elif "destination" in attrib:
            del attrib["destination"]
        return "<{}{}/>".format(self._tag, self._write_attributes(attrib))

    def validate(self, **callbacks):
        super().validate(**callbacks)
        if not self.src:
            title = "Empty Source Field"
            msg = "No source specified, nothing will be installed."
            warn(title, msg, self)


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
        super().validate(**callbacks)
        if self.order is not Order.EXPLICIT:
            title = "Non Explicit Page Order"
            msg = (
                "This installer has {} order, which reorders "
                "the pages during installation. Use Explicit "
                "order to avoid this.".format(self.order.value)
            )
            warn(title, msg, self, critical=True)
        for page in self._page_list:
            if page:
                page.validate(**callbacks)
            else:
                title = "Empty Page"
                msg = "This page is empty and will not be written to prevent errors."
                warn(title, msg, page)


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
        super().validate(**callbacks)
        if self.order is not Order.EXPLICIT:
            title = "Non Explicit Group Order"
            msg = (
                "This page has {} order, which reorders "
                "the groups during installation. Use Explicit "
                "order to avoid this.".format(self.order.value)
            )
            warn(title, msg, self, critical=True)
        if self._conditions:
            self._conditions.validate(**callbacks)
        for group in self._group_list:
            if group:
                group.validate(**callbacks)
            else:
                title = "Empty Group"
                msg = "This group is empty and will not be written to prevent errors."
                warn(title, msg, group)
        if not self._name:
            title = "Empty Page Name"
            msg = "This page has no name."
            warn(title, msg, self)


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
        super().validate(**callbacks)
        if self.order is not Order.EXPLICIT:
            title = "Non Explicit Option Order"
            msg = (
                "This group has {} order, which reorders "
                "the options during installation. Use Explicit "
                "order to avoid this.".format(self.order.value)
            )
            warn(title, msg, self, critical=True)
        for option in self._option_list:
            option.validate(**callbacks)
        if not self._name:
            title = "Empty Group Name"
            msg = "This group has no name."
            warn(title, msg, self)


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
        super().validate(**callbacks)
        if not self.name:
            title = "Empty Option Name"
            msg = "This option has no name."
            warn(title, msg, self)
        if not self.description:
            title = "Empty Option Description"
            msg = "This option has no description."
            warn(title, msg, self)
        if not self.files and not self.flags:
            title = "Option Does Nothing"
            msg = "This option installs no files and sets no flags."
            warn(title, msg, self)
        if self.files:
            self.files.validate(**callbacks)
        if self.flags:
            self.flags.validate(**callbacks)
        if isinstance(self.type, Type):
            self.type.validate(**callbacks)


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
        super().validate(**callbacks)
        if not self:
            title = "Empty Type Descriptor"
            msg = "This type descriptor is empty and will never set a type."
            warn(title, msg, self, critical=True)
        for key in self._map:
            key.validate(**callbacks)


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
        super().validate(**callbacks)
        for key, value in self._map.items():
            key.validate(**callbacks)
            value.validate(**callbacks)
