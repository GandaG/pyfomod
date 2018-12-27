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

from . import base

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
    def __init__(self, quiet=True):
        self.quiet = quiet
        self._stack = []
        self._data = ""
        self._last = None

    def start(self, tag, attrib):
        elem = None
        attrib = dict(attrib)
        with suppress(IndexError):
            parent = self._stack[-1]
        with suppress(IndexError):
            gparent = self._stack[-2]
        if tag == "config":
            elem = base.Root(attrib)
        elif tag == "fomod":
            elem = base.Info(attrib)
        elif tag == "moduleName":
            elem = base.Name(attrib)
            parent._name = elem
        elif tag in ("moduleDependencies", "dependencies", "visible"):
            elem = base.Conditions(attrib)
            elem.type = base.ConditionType(attrib.get("operator", "And"))
            if isinstance(parent, base.Conditions):  # nested dependencies
                parent[elem] = None
            else:
                parent.conditions = elem
        elif tag == "requiredInstallFiles":
            elem = base.Files(attrib)
            parent.files = elem
        elif tag in ("file", "folder"):
            elem = base.File(tag, attrib)
            elem.src = attrib["source"]
            elem.dst = attrib.get("destination", "")
            parent._file_list.append(elem)
        elif tag == "installSteps":
            elem = base.Pages(attrib)
            elem.order = base.Order(attrib.get("order", "Ascending"))
            parent.pages = elem
        elif tag == "installStep":
            elem = base.Page(attrib)
            elem.name = attrib["name"]
            parent._page_list.append(elem)
        elif tag == "group":
            elem = base.Group(attrib)
            elem.name = attrib["name"]
            elem.type = base.GroupType(attrib["type"])
            gparent._group_list.append(elem)
        elif tag == "plugin":
            elem = base.Option(attrib)
            elem.name = attrib["name"]
            gparent._option_list.append(elem)
        elif tag == "files":
            elem = base.Files(attrib)
            if isinstance(parent, base.Option):
                parent.files = elem
            else:  # under pattern tag
                parent.value = elem
        elif tag == "conditionFlags":
            elem = base.Flags(attrib)
            parent.flags = elem
        elif tag == "dependencyType":
            elem = base.Type(attrib)
            gparent.type = elem
        elif tag == "conditionalFileInstalls":
            elem = base.FilePatterns(attrib)
            parent.file_patterns = elem
        elif tag == "pattern":
            elem = PatternPlaceholder(attrib)
        else:
            elem = Placeholder(tag, attrib)
        self._stack.append(elem)
        return elem

    def data(self, data):
        self._data = data.strip()

    def end(self, tag):
        elem = self._stack.pop()
        assert tag == elem._tag
        with suppress(IndexError):
            parent = self._stack[-1]
        with suppress(IndexError):
            gparent = self._stack[-2]
        if isinstance(elem, Placeholder):
            parent._children[elem._tag] = (elem._attrib, self._data)
        if tag == "moduleName":
            elem.name = self._data
        elif tag == "fileDependency":
            fname = elem._attrib["file"]
            ftype = base.FileType(elem._attrib["state"])
            parent[fname] = ftype
        elif tag == "flagDependency":
            fname = elem._attrib["flag"]
            fvalue = elem._attrib["value"]
            parent[fname] = fvalue
        elif tag == "gameDependency":
            parent[None] = elem._attrib["version"]
        elif tag in ("optionalFileGroups", "plugins"):
            order = elem._attrib.get("order", "Ascending")
            parent._order = base.Order(order)
        elif tag == "description":
            parent._description = self._data
        elif tag == "image":
            parent._image = elem._attrib["path"]
        elif tag == "flag":
            parent._map[elem._attrib["name"]] = self._data
        elif tag == "type":
            if isinstance(gparent, base.Option):
                gparent._type = base.OptionType(elem._attrib["name"])
            else:  # under pattern tag
                parent.value = base.OptionType(elem._attrib["name"])
        elif tag == "defaultType":
            parent._default = base.OptionType(elem._attrib["name"])
        elif tag == "pattern":
            gparent[elem.conditions] = elem.value
        self._data = ""
        self._last = elem
        return elem

    def comment(self, text):
        if text and not self.quiet:
            title = "Comment Detected"
            msg = "There are comments in this fomod, they will be ignored."
            base.warn(title, msg, None, critical=True)

    def close(self):
        assert not self._stack
        assert isinstance(self._last, (base.Root, base.Info))
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


def parse(source, quiet=True, lineno=False):
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
    if not quiet:
        schema = etree.XMLSchema(etree.parse(str(SCHEMA_PATH)))
        try:
            etree.parse(conf, etree.XMLParser(schema=schema))
        except etree.XMLSyntaxError as exc:
            base.warn("Syntax Error", str(exc), None, critical=True)
    parser_target = Target(quiet)
    if lineno:
        root = _iterparse(conf, parser_target)
        if info is not None:
            root._info = _iterparse(conf, parser_target)
    else:
        parser = etree.XMLParser(target=Target(quiet))
        root = etree.parse(conf, parser)
        if info is not None:
            root._info = etree.parse(info, parser)
    if not quiet and info is None:
        base.warn(
            "Missing Info",
            "Info.xml is missing from the fomod subfolder.",
            None,
            critical=True,
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
