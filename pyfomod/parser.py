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

import errno
import os
from collections import OrderedDict
from contextlib import suppress
from pathlib import Path

from lxml import etree

from .fomod import (
    Conditions,
    ConditionType,
    File,
    FilePatterns,
    Files,
    FileType,
    Flags,
    Group,
    GroupType,
    Image,
    Info,
    Name,
    Option,
    OptionType,
    Order,
    Page,
    Pages,
    Root,
    Type,
    ValidationWarning,
)

SCHEMA_PATH = Path(__file__).parent / "fomod.xsd"


class Placeholder(object):
    def __init__(self, tag, attrib):
        self._tag = tag
        self._attrib = attrib
        self._children = OrderedDict()


class PatternPlaceholder(Placeholder):
    def __init__(self, attrib):
        super().__init__("pattern", attrib)
        self.conditions = None
        self.value = None


class Target(object):
    def __init__(self, warnings=None):
        self.warnings = warnings
        self._stack = []
        self._data = []
        self._last = None

    def start(self, tag, attrib):
        attrib = dict(attrib)
        with suppress(IndexError):
            parent = self._stack[-1]
        with suppress(IndexError):
            gparent = self._stack[-2]
        if tag == "config":
            elem = Root(attrib)
        elif tag == "fomod":
            elem = Info(attrib)
        elif tag == "moduleName":
            elem = Name(attrib)
            parent._name = elem
        elif tag == "moduleImage":
            elem = Image(attrib)
            parent._image = elem
        elif tag in ("moduleDependencies", "dependencies", "visible"):
            elem = Conditions(attrib)
            elem.type = ConditionType(attrib.get("operator", "And"))
            if isinstance(parent, Conditions):  # nested dependencies
                parent[elem] = None
            else:
                parent.conditions = elem
        elif tag == "requiredInstallFiles":
            elem = Files(attrib)
            parent.files = elem
        elif tag in ("file", "folder"):
            elem = File(tag, attrib)
            elem.src = attrib["source"]
            elem.dst = attrib.get("destination", None)
            parent._file_list.append(elem)
        elif tag == "installSteps":
            elem = Pages(attrib)
            elem.order = Order(attrib.get("order", "Ascending"))
            parent.pages = elem
        elif tag == "installStep":
            elem = Page(attrib)
            elem.name = attrib["name"]
            parent._page_list.append(elem)
        elif tag == "group":
            elem = Group(attrib)
            elem.name = attrib["name"]
            elem.type = GroupType(attrib["type"])
            gparent._group_list.append(elem)
        elif tag == "plugin":
            elem = Option(attrib)
            elem.name = attrib["name"]
            gparent._option_list.append(elem)
        elif tag == "files":
            elem = Files(attrib)
            if isinstance(parent, Option):
                parent.files = elem
            else:  # under pattern tag
                parent.value = elem
        elif tag == "conditionFlags":
            elem = Flags(attrib)
            parent.flags = elem
        elif tag == "dependencyType":
            elem = Type(attrib)
            gparent.type = elem
        elif tag == "conditionalFileInstalls":
            elem = FilePatterns(attrib)
            parent.file_patterns = elem
        elif tag == "pattern":
            elem = PatternPlaceholder(attrib)
        else:
            elem = Placeholder(tag, attrib)
        self._stack.append(elem)
        return elem

    def data(self, data):
        self._data.append(data)

    def end(self, tag):
        elem = self._stack.pop()
        assert tag == elem._tag
        with suppress(IndexError):
            parent = self._stack[-1]
        with suppress(IndexError):
            gparent = self._stack[-2]

        data = "".join(self._data).strip()
        del self._data[:]

        if isinstance(elem, Placeholder):
            parent._children[elem._tag] = (elem._attrib, data)
        if tag == "moduleName":
            elem.name = data
        elif tag == "fileDependency":
            fname = elem._attrib["file"]
            ftype = FileType(elem._attrib["state"])
            parent[fname] = ftype
        elif tag == "flagDependency":
            fname = elem._attrib["flag"]
            fvalue = elem._attrib["value"]
            parent[fname] = fvalue
        elif tag == "gameDependency":
            parent[None] = elem._attrib["version"]
        elif tag in ("optionalFileGroups", "plugins"):
            order = elem._attrib.get("order", "Ascending")
            parent._order = Order(order)
        elif tag == "description":
            parent._description = data
        elif tag == "image":
            parent._image = elem._attrib["path"]
        elif tag == "flag":
            parent._map[elem._attrib["name"]] = data
        elif tag == "type":
            if isinstance(gparent, Option):
                gparent._type = OptionType(elem._attrib["name"])
            else:  # under pattern tag
                parent.value = OptionType(elem._attrib["name"])
        elif tag == "defaultType":
            parent._default = OptionType(elem._attrib["name"])
        elif tag == "pattern":
            gparent[elem.conditions] = elem.value
        self._last = elem
        return elem

    def comment(self, text):
        if text and self.warnings is not None:
            title = "Comment Detected"
            msg = "There are comments in this fomod, they will be ignored."
            self.warnings.append(ValidationWarning(title, msg, None, critical=True))

    def close(self):
        assert not self._stack
        assert isinstance(self._last, (Root, Info))
        return self._last


def _iterparse(file_path, target):
    events = ("start", "end")
    for event, element in etree.iterparse(file_path, events=events):
        if event == "start":
            new_elem = target.start(element.tag, element.attrib)
            new_elem._lineno = element.sourceline
            if element.text is not None:
                target.data(element.text)
        elif event == "end":
            target.end(element.tag)
    return target.close()


def parse(source, warnings=None, lineno=False):
    if isinstance(source, (tuple, list)):
        info, conf = source
    else:
        path = Path(source) / "fomod"
        if not path.is_dir():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), "fomod")
        info = path / "info.xml"
        conf = path / "moduleconfig.xml"
        if not info.is_file():
            info = None
        else:
            info = str(info)
        if not conf.is_file():
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), "moduleconfig.xml"
            )
        else:
            conf = str(conf)
    if warnings is not None:
        schema = etree.XMLSchema(etree.parse(str(SCHEMA_PATH)))
        try:
            etree.parse(conf, etree.XMLParser(schema=schema))
        except etree.XMLSyntaxError as exc:
            msg = str(exc)
            if str(exc).endswith(" (<string>, line 0)"):
                msg = msg[:-19]
            warnings.append(ValidationWarning("Syntax Error", msg, None, critical=True))
    parser_target = Target(warnings)
    if lineno:
        root = _iterparse(conf, parser_target)
        if info is not None:
            root._info = _iterparse(conf, parser_target)
    else:
        parser = etree.XMLParser(target=Target(warnings))
        root = etree.parse(conf, parser)
        if info is not None:
            root._info = etree.parse(info, parser)
    if info is None and warnings is not None:
        warnings.append(
            ValidationWarning(
                "Missing Info",
                "Info.xml is missing from the fomod subfolder.",
                None,
                critical=True,
            )
        )
    return root


def write(root, path):
    if isinstance(path, (tuple, list)):
        info = path[0]
        if info is not None:
            info = Path(info)
        conf = Path(path[1])
    else:
        path = Path(path) / "fomod"
        path.mkdir(parents=True, exist_ok=True)
        info = path / "info.xml"
        conf = path / "moduleconfig.xml"
    if info is not None:
        with info.open("w") as info_f:
            info_f.write(root._info.to_string())
            info_f.write("\n")
    with conf.open("w") as conf_f:
        conf_f.write(root.to_string())
        conf_f.write("\n")
