# Copyright 2019 Daniel Nunes
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

from enum import Enum, IntEnum, auto


class ErrorKind(IntEnum):
    # Note is for anything that, while it won't produce errors while
    # installing is probably not what the fomod author intended.
    NOTE = auto()
    # Warning is for anything that either may cause issues during
    # installation or may have undefined behaviour.
    WARNING = auto()
    # Error is for anything that will reliably produce errors or
    # issues when installing.
    ERROR = auto()


class ErrorID(Enum):
    INVALID_ENUM = (
        "Invalid {name} Attribute",
        "{name} was set to '{actual}' in tag "
        "'{tag}' but can only be one of: '{values}'. It was "
        "set to default '{default}'.",
    )
    DEFAULT_ATTRIBUTE = (
        "Missing {title} Attribute",
        "The '{attribute}' attribute on the '{tag}' "
        "tag is required. It was set to '{default}'.",
    )
    REQUIRED_ATTRIBUTE = (
        "Missing {title} Attribute",
        "The '{attribute}' attribute on the '{tag}' "
        "tag is required. This tag will be skipped.",
    )
    COMMENTS_PRESENT = (
        "XML Comments Present",
        "There are comments in the fomod, they will be ignored.",
    )
    INVALID_SYNTAX = ("XML Syntax Error", "{error_msg}")
    MISSING_INFO = ("Missing Info XML", "Info.xml is missing from the fomod subfolder.")
    EMPTY_TREE = ("Empty Fomod Tree", "This fomod is empty, nothing will be installed.")
    IMPOSSIBLE_FLAG = ("Impossible Flag", "The flag '{name}' is never created or set.")
    EMPTY_ELEMENT = ("Empty {title}", "{error_msg}")
    MISSING_NAME = ("Missing {title} Name", "The {nameless} does not have a name.")
    MISSING_DESCRIPTION = (
        "Missing Option Description",
        "The option '{name}' does not have a description.",
    )
    MISSING_DESTINATION = (
        "Missing Destination Field",
        "There is no destination on the '{name}' file element. "
        "If omitted, the destination is the same as "
        "the source. This may not be intended.",
    )
    NON_EXPLICIT_ORDER = (
        "Non Explicit Order",
        "This element has '{order}' order, "
        "which reorders the child elements during "
        "installation. Use Explicit order to avoid this.",
    )
    TOO_FEW_OPTIONS = (
        "Not Enough Selectable Options",
        "The group '{name}' needs {group_type} "
        "selectable option but none are available.",
    )
    TOO_MANY_OPTIONS = (
        "Too Many Required Options",
        "The group '{name}' can only have {group_type} "
        "selected option but at least two are required.",
    )


class FomodError(object):
    def __init__(self, kind, id, elem, **format):
        self.kind = ErrorKind(kind)
        self.elem = elem
        self.line = getattr(elem, "lineno", None)
        self.id = ErrorID(id)
        self.title = self.id.value[0].format(**format)
        self.msg = self.id.value[1].format(**format)

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return (
                self.kind is other.kind
                and self.elem is other.elem
                and self.id is other.id
                and self.title == other.title
                and self.msg == other.msg
            )
        return NotImplemented

    def __repr__(self):
        return (
            f"'<{type(self).__name__}(kind={self.kind.name}, "
            f"elem={repr(self.elem)}, id={self.id.name}, "
            f"title={self.title}, msg={self.msg}) at {id(self)}>'"
        )
