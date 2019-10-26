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

import re


class ValidationWarning(object):
    def __init__(self, title, msg, elem, critical=False):
        self.title = title
        self.msg = msg
        self.elem = elem
        self.critical = critical

    def __eq__(self, other):
        if isinstance(other, ValidationWarning):
            return (
                self.title == other.title
                and self.msg == other.msg
                and self.elem == other.elem
                and self.critical == other.critical
            )
        return NotImplemented

    def __repr__(self):
        return (
            f"'<{type(self).__name__}({repr(self.title)}, "
            f"{repr(self.msg)}, {repr(self.elem)}, "
            f"critical={repr(self.critical)}) at {id(self)}>'"
        )


class InvalidEnumWarning(ValidationWarning):
    def __init__(self, tag, enum_, actual, elem):
        # split camel case enum names into title
        enum_name = " ".join(
            re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", enum_.__name__)
        )
        enum_values = "', '".join(x.value for x in enum_)
        enum_default = enum_.default().value
        title = f"Invalid {enum_name}"
        msg = (
            f"{enum_name} was set to '{actual}' in "
            f"tag '{tag}' but can only be one of: "
            f"'{enum_values}'. "
            f"It was set to default '{enum_default}'."
        )
        super().__init__(title, msg, elem, critical=True)


class DefaultAttributeWarning(ValidationWarning):
    def __init__(self, tag, attribute, default, elem):
        title = f"Missing {attribute.title()} Attribute"
        msg = (
            f"The '{attribute}' attribute on the '{tag}' "
            f"tag is required. It was set to '{default}'."
        )
        super().__init__(title, msg, elem, critical=True)


class RequiredAttributeWarning(ValidationWarning):
    def __init__(self, tag, attribute):
        title = f"Missing {attribute.title()} Attribute"
        msg = (
            f"The '{attribute}' attribute on the '{tag}' "
            f"tag is required. This tag will be skipped."
        )
        super().__init__(title, msg, None, critical=True)


class CommentsPresentWarning(ValidationWarning):
    def __init__(self):
        title = "XML Comments Present"
        msg = "There are comments in the fomod, they will be ignored."
        super().__init__(title, msg, None, critical=True)


class InvalidSyntaxWarning(ValidationWarning):
    def __init__(self, error_msg):
        title = "XML Syntax Error"
        msg = error_msg.replace(" (<string>, line 0)", "")
        super().__init__(title, msg, None, critical=True)


class MissingInfoWarning(ValidationWarning):
    def __init__(self):
        title = "Missing Info XML"
        msg = "Info.xml is missing from the fomod subfolder."
        super().__init__(title, msg, None, critical=False)


class EmptyTreeWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Fomod Tree"
        msg = "This fomod is empty, nothing will be installed."
        super().__init__(title, msg, elem, critical=False)


class ImpossibleFlagWarning(ValidationWarning):
    def __init__(self, flag_name, elem):
        title = "Impossible Flag"
        msg = f"The flag '{flag_name}' is never created or set."
        super().__init__(title, msg, elem, critical=True)


class InstallerNameWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Missing Installer Name"
        msg = "This fomod does not have a name."
        super().__init__(title, msg, elem, critical=False)


class EmptyConditionsWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Conditions"
        msg = "This element should have at least one condition present."
        super().__init__(title, msg, elem, critical=False)


class VersionDependencyWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Version Dependency"
        msg = "This version dependency is empty."
        super().__init__(title, msg, elem, critical=False)


class FileDependencyWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty File Dependency"
        msg = "This file dependency depends on no file, may not work correctly."
        super().__init__(title, msg, elem, critical=False)


class UselessFlagsWarning(ValidationWarning):
    def __init__(self, flag_name, elem):
        title = "Impossible Flag"
        msg = f"Flag {flag_name} shouldn't be used here since it can't have been set."
        super().__init__(title, msg, elem, critical=True)


class EmptySourceWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Source Field"
        msg = "No source specified, this could lead to problems installing."
        super().__init__(title, msg, elem, critical=True)


class MissingDestinationWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Missing Destination Field"
        msg = (
            "If omitted, the destination is the same as "
            "the source. This may not be intended."
        )
        super().__init__(title, msg, elem, critical=False)


class OrderWarning(ValidationWarning):
    def __init__(self, order, elem):
        title = "Non Explicit Order"
        msg = (
            f"This element has {order.value} order, "
            "which reorders the child elements during "
            "installation. Use Explicit order to avoid this."
        )
        super().__init__(title, msg, elem, critical=False)


class EmptyPageWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Page"
        msg = "This page is empty."
        super().__init__(title, msg, elem, critical=False)


class PageNameWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Page Name"
        msg = "This page has no name."
        super().__init__(title, msg, elem, critical=False)


class EmptyGroupWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Group"
        msg = "This group is empty."
        super().__init__(title, msg, elem, critical=False)


class GroupNameWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Group Name"
        msg = "This group has no name."
        super().__init__(title, msg, elem, critical=False)


class AtLeastOneWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Not Enough Selectable Options"
        msg = "This group needs at least one selectable option but none are available."
        super().__init__(title, msg, elem, critical=True)


class ExactlyOneMissingWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Not Enough Selectable Options"
        msg = "This group needs exactly one selectable option but none are available."
        super().__init__(title, msg, elem, critical=True)


class ExactlyOneRequiredWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Too Many Required Options"
        msg = (
            "This group can only have exactly one option "
            "selected but at least two are required."
        )
        super().__init__(title, msg, elem, critical=True)


class AtMostOneWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Too Many Required Options"
        msg = (
            "This group can have one option selected "
            "at most but at least two are required."
        )
        super().__init__(title, msg, elem, critical=True)


class OptionNameWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Option Name"
        msg = "This option has no name."
        super().__init__(title, msg, elem, critical=False)


class OptionDescriptionWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Option Description"
        msg = "This option has no description."
        super().__init__(title, msg, elem, critical=False)


class EmptyOptionWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Option Does Nothing"
        msg = "This option installs no files and sets no flags."
        super().__init__(title, msg, elem, critical=False)


class EmptyTypeWarning(ValidationWarning):
    def __init__(self, elem):
        title = "Empty Type Descriptor"
        msg = "This type descriptor is empty and will never set a type."
        super().__init__(title, msg, elem, critical=True)
