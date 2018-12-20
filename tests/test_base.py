import textwrap
from collections import OrderedDict

import pytest
from pyfomod import base


def test_warn():
    with pytest.warns(base.ValidationWarning, match="Title - Msg"):
        base.warn("Title", "Msg", None)
    with pytest.warns(base.CriticalWarning):
        base.warn("", "", None, critical=True)


class Test_HashableSequence:
    class Seq(base.HashableSequence):
        def __init__(self):
            self.list = []

        def __getitem__(self, key):
            return self.list[key]

        def __setitem__(self, key, value):
            self.list[key] = value

        def __delitem__(self, key):
            del self.list[key]

        def __len__(self):
            return len(self.list)

        def insert(self, index, value):
            self.list.insert(index, value)

    def setup_method(self):
        self.seq = self.Seq()
        self.seq.extend([1, 2, 3])

    def test_iter(self):
        assert list(self.seq) == [1, 2, 3]

    def test_contains(self):
        assert 2 in self.seq

    def test_reversed(self):
        assert list(reversed(self.seq)) == [3, 2, 1]

    def test_index(self):
        assert self.seq.index(2) == 1

    def test_count(self):
        assert self.seq.count(2) == 1

    def test_append(self):
        self.seq.append(4)
        assert 4 in self.seq
        assert list(self.seq) == [1, 2, 3, 4]

    def test_clear(self):
        self.seq.clear()
        assert not self.seq

    def test_reverse(self):
        self.seq.reverse()
        assert list(self.seq) == [3, 2, 1]

    def test_extend(self):
        self.seq.extend([4, 5])
        assert list(self.seq) == [1, 2, 3, 4, 5]

    def test_pop(self):
        assert self.seq.pop() == 3
        assert list(self.seq) == [1, 2]

    def test_remove(self):
        self.seq.remove(2)
        assert list(self.seq) == [1, 3]

    def test_iadd(self):
        self.seq += [4, 5]
        assert list(self.seq) == [1, 2, 3, 4, 5]


class Test_HashableMapping:
    class Hash(base.HashableMapping):
        def __init__(self):
            self.dict = {}

        def __getitem__(self, key):
            return self.dict[key]

        def __setitem__(self, key, value):
            self.dict[key] = value

        def __delitem__(self, key):
            del self.dict[key]

        def __iter__(self):
            return iter(self.dict)

        def __len__(self):
            return len(self.dict)

    def setup_method(self):
        self.hash = self.Hash()
        self.hash.dict.update({1: "1", 2: "2", 3: "3"})

    def test_contains(self):
        assert 2 in self.hash.dict

    def test_keys(self):
        assert list(self.hash.keys()) == [1, 2, 3]

    def test_items(self):
        assert list(self.hash.items()) == [(1, "1"), (2, "2"), (3, "3")]

    def test_values(self):
        assert list(self.hash.values()) == ["1", "2", "3"]

    def test_get(self):
        assert self.hash.get(2) == "2"
        assert self.hash.get(4) is None

    def test_pop(self):
        assert self.hash.pop(2) == "2"
        assert dict(self.hash) == {1: "1", 3: "3"}

    def test_popitem(self):
        self.hash.popitem()
        assert dict(self.hash) == {2: "2", 3: "3"}

    def test_clear(self):
        self.hash.clear()
        assert dict(self.hash) == {}

    def test_update(self):
        self.hash.update({4: "4"})
        assert dict(self.hash) == {1: "1", 2: "2", 3: "3", 4: "4"}

    def test_setdefault(self):
        assert self.hash.setdefault(2) == "2"
        assert self.hash.setdefault(4, "4") == "4"


class Test_BaseFomod:
    def test_write_attributes(self):
        attrib = {"boop": "beep", "value": "1"}
        expected = ' boop="beep" value="1"'
        assert base.BaseFomod._write_attributes(attrib) == expected

    def test_write_children(self):
        children = OrderedDict(
            [("first", ({}, "text")), ("second", ({"beep": "boop"}, ""))]
        )
        expected = '\n<first>text</first>\n<second beep="boop"/>'
        test = base.BaseFomod("", {})
        test._children = children
        assert test._write_children() == expected


class Test_Root:
    def setup_method(self):
        self.root = base.Root()

    def test_name(self):
        self.root.name = "beep"
        assert self.root.name == "beep"
        assert self.root._name.name == "beep"

    def test_author(self):
        self.root.author = "boop"
        assert self.root.author == "boop"
        assert "Author" in self.root._info._children
        assert self.root._info._children["Author"] == ({}, "boop")

    def test_version(self):
        self.root.version = "boop"
        assert self.root.version == "boop"
        assert "Version" in self.root._info._children
        assert self.root._info._children["Version"] == ({}, "boop")

    def test_description(self):
        self.root.description = "boop"
        assert self.root.description == "boop"
        assert "Description" in self.root._info._children
        assert self.root._info._children["Description"] == ({}, "boop")

    def test_website(self):
        self.root.website = "boop"
        assert self.root.website == "boop"
        assert "Website" in self.root._info._children
        assert self.root._info._children["Website"] == ({}, "boop")

    def test_conditions(self):
        test = base.Conditions()
        self.root.conditions = test
        assert self.root.conditions is test
        assert self.root._conditions is test
        assert test._tag == "moduleDependencies"

    def test_files(self):
        test = base.Files()
        self.root.files = test
        assert self.root.files is test
        assert self.root._files is test
        assert test._tag == "requiredInstallFiles"

    def test_pages(self):
        test = base.Pages()
        self.root.pages = test
        assert self.root.pages is test
        assert self.root._pages is test

    def test_file_patterns(self):
        test = base.FilePatterns()
        self.root.file_patterns = test
        assert self.root.file_patterns is test
        assert self.root._file_patterns is test

    def test_to_string(self):
        self.root._children = OrderedDict([("child", ({"beep": "boop"}, ""))])
        self.root.name = "Name"
        expected = textwrap.dedent(
            """\
            <config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">
              <moduleName>Name</moduleName>
              <child beep="boop"/>
            </config>"""
        )
        assert self.root.to_string() == expected

    def test_validate(self):
        warn_msg = "Empty Installer - This fomod is empty, nothing will be installed"
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.root.validate()
        page = base.Page()
        page.conditions["boop"] = "beep"
        page.append(base.Group())
        self.root.pages.append(page)
        warn_msg = 'Impossible Flags - The flag "boop" is never created or set'
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.root.validate()


class Test_Info:
    def setup_method(self):
        self.info = base.Info()

    def test_get_text(self):
        self.info._children["Key"] = ({}, "boop")
        assert self.info.get_text("key") == "boop"
        assert self.info.get_text("Key") == "boop"

    def test_set_text(self):
        self.info._children["Key"] = ({}, "boop")
        self.info.set_text("Key", "beep")
        assert self.info._children == {"Key": ({}, "beep")}
        self.info.set_text("New", "beepity")
        assert self.info._children["New"] == ({}, "beepity")

    def test_to_string(self):
        self.info._children["Author"] = ({}, "None")
        expected = textwrap.dedent(
            """\
                <fomod>
                  <Author>None</Author>
                </fomod>"""
        )
        assert self.info.to_string() == expected


class Test_Name:
    def setup_method(self):
        self.name = base.Name()

    def test_to_string(self):
        self.name._attrib = {"first": "second"}
        self.name.name = "Name"
        expected = '<moduleName first="second">Name</moduleName>'
        assert self.name.to_string() == expected

    def test_validate(self):
        warn_msg = "Missing Installer Name - This fomod does not have a name."
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.name.validate()


class Test_Conditions:
    def setup_method(self):
        self.cond = base.Conditions()

    def test_type(self):
        self.cond.type = base.ConditionType.OR
        assert self.cond.type is base.ConditionType.OR
        assert self.cond._type is base.ConditionType.OR

    def test_to_string(self):
        self.cond.type = base.ConditionType.OR
        self.cond[None] = "1.0"
        self.cond["boop"] = "beep"
        nest = base.Conditions()
        nest.type = base.ConditionType.AND
        nest["file"] = base.FileType.MISSING
        self.cond[nest] = None
        expected = textwrap.dedent(
            """\
                <dependencies operator="Or">
                  <gameDependency version="1.0"/>
                  <flagDependency flag="boop" value="beep"/>
                  <dependencies operator="And">
                    <fileDependency file="file" state="Missing"/>
                  </dependencies>
                </dependencies>"""
        )
        self.cond.to_string() == expected

    def test_validate(self):
        warn_msg = (
            "Empty Conditions - This element should have "
            "at least one condition present."
        )
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.cond.validate()
        nest = base.Conditions()
        self.cond[nest] = None
        warn_msg = (
            "Empty Conditions - This element is empty and "
            "will not be written to prevent errors."
        )
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.cond.validate()
        self.cond[None] = ""
        warn_msg = (
            "Empty Version Dependency - This version dependency "
            "is empty and may not work correctly."
        )
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.cond.validate()
        self.cond[""] = base.FileType.ACTIVE
        warn_msg = (
            "Empty File Dependency - This file dependency depends "
            "on no file, may not work correctly."
        )
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.cond.validate()
        self.cond._tag = "moduleDependencies"
        self.cond["boop"] = "beep"
        warn_msg = (
            "Useless Flags - Flag boop shouldn't be used here "
            "since it can't have been set."
        )
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.cond.validate()


class Test_Files:
    def setup_method(self):
        self.files = base.Files()

    def test_getitem(self):
        item1 = base.File("file")
        item1.src = "boop"
        item1.dst = "boopity"
        item2 = base.File("folder")
        item2.src = "beep"
        item2.dst = "beepity"
        self.files._file_list.extend([item1, item2])
        assert self.files["boop"] == "boopity"
        assert self.files["beep/"] == "beepity"

    def test_setitem(self):
        self.files["boop"] = ""
        assert self.files._file_list[0]._tag == "file"
        self.files._file_list.clear()
        self.files["beep/"] = ""
        assert self.files._file_list[0]._tag == "folder"

    def test_delitem(self):
        item1 = base.File("file")
        item1.src = "boop"
        item1.dst = "boopity"
        item2 = base.File("folder")
        item2.src = "beep"
        item2.dst = "beepity"
        self.files._file_list.extend([item1, item2])
        assert list(self.files.keys()) == ["boop", "beep/"]
        del self.files["beep/"]
        assert list(self.files.keys()) == ["boop"]

    def test_to_string(self):
        self.files["boop"] = "boopity"
        self.files["beep/"] = "beepity"
        expected = textwrap.dedent(
            """\
                <files>
                  <file source="boop" destination="boopity"/>
                  <folder source="beep" destination="beepity"/>
                </files>"""
        )
        assert self.files.to_string() == expected


class Test_File:
    def setup_method(self):
        self.file = base.File()

    def test_to_string(self):
        self.file._tag = "file"
        self.file.src = "src"
        self.file.dst = "dst"
        expected = '<file source="src" destination="dst"/>'
        self.file.to_string() == expected
        self.file.dst = ""
        expected = '<file source="src"/>'
        self.file.to_string() == expected

    def test_validate(self):
        warn_msg = (
            "Empty Source Field - No source specified, nothing will be installed."
        )
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.file.validate()


class Test_Pages:
    def setup_method(self):
        self.pages = base.Pages()

    def test_order(self):
        self.pages.order = base.Order.EXPLICIT
        assert self.pages.order is base.Order.EXPLICIT
        assert self.pages._order is base.Order.EXPLICIT

    def test_to_string(self):
        page1 = base.Page()
        page1.append(base.Group())
        page1.name = "boop"
        text = page1.to_string()
        page2 = base.Page()
        self.pages.extend([page1, page2])
        expected = textwrap.dedent(
            """\
                <installSteps order="Explicit">
{}
                </installSteps>""".format(
                textwrap.indent(text, "    " * 4 + "  ")
            )
        )
        assert self.pages.to_string() == expected

    def test_validate(self):
        self.pages.append(base.Page())
        warn_msg = (
            "Empty Page - This page is empty and will not be written to prevent errors."
        )
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.pages.validate()


class Test_Page:
    def setup_method(self):
        self.page = base.Page()

    def test_name(self):
        self.page.name = "boop"
        assert self.page.name == "boop"
        assert self.page._name == "boop"

    def test_conditions(self):
        test = base.Conditions()
        self.page.conditions = test
        assert self.page.conditions is test
        assert self.page._conditions is test

    def test_order(self):
        self.page.order = base.Order.EXPLICIT
        assert self.page.order is base.Order.EXPLICIT
        assert self.page._order is base.Order.EXPLICIT

    def test_to_string(self):
        group1 = base.Group()
        group1.append(base.Option())
        text = group1.to_string()
        group2 = base.Group()
        self.page.extend([group1, group2])
        self.page.name = "boop"
        self.page.order = base.Order.ASCENDING
        expected = textwrap.dedent(
            """\
                <installStep name="boop">
                  <optionalFileGroups order="Ascending">
{}
                  </optionalFileGroups>
                </installStep>""".format(
                textwrap.indent(text, "    " * 5)
            )
        )
        assert self.page.to_string() == expected

    def test_validate(self):
        warn_msg = "Empty Page Name - This page has no name."
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.page.validate()
        self.page.append(base.Group())
        warn_msg = (
            "Empty Group - This group is empty and will "
            "not be written to prevent errors."
        )
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.page.validate()


class Test_Group:
    def setup_method(self):
        self.group = base.Group()

    def test_name(self):
        self.group.name = "boop"
        assert self.group.name == "boop"
        assert self.group._name == "boop"

    def test_order(self):
        self.group.order = base.Order.EXPLICIT
        assert self.group.order is base.Order.EXPLICIT
        assert self.group._order is base.Order.EXPLICIT

    def test_type(self):
        self.group.type = base.GroupType.ALL
        assert self.group.type is base.GroupType.ALL
        assert self.group._type is base.GroupType.ALL

    def test_to_string(self):
        option1 = base.Option()
        option1_text = option1.to_string()
        self.group.append(option1)
        self.group.name = "name"
        self.group.order = base.Order.DESCENDING
        self.group.type = base.GroupType.ALL
        expected = textwrap.dedent(
            """\
                <group name="name" type="SelectAll">
                  <plugins order="Descending">
{}
                  </plugins>
                </group>""".format(
                textwrap.indent(option1_text, "    " * 5)
            )
        )
        assert self.group.to_string() == expected

    def test_validate(self):
        warn_msg = "Empty Group Name - This group has no name."
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.group.validate()


class Test_Option:
    def setup_method(self):
        self.option = base.Option()

    def test_name(self):
        self.option.name = "boop"
        assert self.option.name == "boop"
        assert self.option._name == "boop"

    def test_description(self):
        self.option.description = "aa"
        assert self.option.description == "aa"
        assert self.option._description == "aa"

    def test_image(self):
        self.option.image = "path"
        assert self.option.image == "path"
        assert self.option._image == "path"

    def test_files(self):
        test = base.Files()
        self.option.files = test
        assert self.option.files is test
        assert self.option._files is test

    def test_flags(self):
        test = base.Flags()
        self.option.flags = test
        assert self.option.flags is test
        assert self.option._flags is test

    def test_type(self):
        self.option.type = base.OptionType.REQUIRED
        assert self.option.type is base.OptionType.REQUIRED
        assert self.option._type is base.OptionType.REQUIRED
        test = base.Type()
        self.option.type = test
        assert self.option.type is test
        assert self.option._type is test

    def test_to_string(self):
        self.option.name = "boo"
        self.option.description = "bee"
        self.option.image = "path"
        self.option.type = base.OptionType.RECOMMENDED
        files = base.Files()
        files["src"] = "dst"
        files_text = files.to_string()
        self.option.files = files
        flags = base.Flags()
        flags["flag"] = "value"
        flags_text = flags.to_string()
        self.option.flags = flags
        expected = textwrap.dedent(
            """\
                <plugin name="boo">
                  <description>bee</description>
                  <image path="path"/>
{}
{}
                  <typeDescriptor>
                    <type name="Recommended"/>
                  </typeDescriptor>
                </plugin>""".format(
                textwrap.indent(files_text, "    " * 4 + "  "),
                textwrap.indent(flags_text, "    " * 4 + "  "),
            )
        )
        assert self.option.to_string() == expected

    def test_validate(self):
        warn_msg = "Empty Option Name - This option has no name."
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.option.validate()
        warn_msg = "Empty Option Description - This option has no description."
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.option.validate()
        warn_msg = (
            "Option Does Nothing - This option installs no files and sets no flags."
        )
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.option.validate()


class Test_Flags:
    def setup_method(self):
        self.flags = base.Flags()

    def test_to_string(self):
        self.flags["flag"] = "value"
        expected = textwrap.dedent(
            """\
                <conditionFlags>
                  <flag name="flag">value</flag>
                </conditionFlags>"""
        )
        assert self.flags.to_string() == expected


class Test_Type:
    def setup_method(self):
        self.type = base.Type()

    def test_default(self):
        self.type.default = base.OptionType.RECOMMENDED
        assert self.type.default is base.OptionType.RECOMMENDED
        assert self.type._default is base.OptionType.RECOMMENDED

    def test_to_string(self):
        self.type.default = base.OptionType.REQUIRED
        cond = base.Conditions()
        cond["flag"] = "value"
        self.type[cond] = base.OptionType.RECOMMENDED
        text = cond.to_string()
        expected = textwrap.dedent(
            """\
                <dependencyType>
                  <defaultType name="Required"/>
                  <patterns>
                    <pattern>
{}
                      <type name="Recommended"/>
                    </pattern>
                  </patterns>
                </dependencyType>""".format(
                textwrap.indent(text, "    " * 5 + "  ")
            )
        )
        assert self.type.to_string() == expected

    def test_validate(self):
        warn_msg = (
            "Empty Type Descriptor - This type descriptor "
            "is empty and will never set a type."
        )
        with pytest.warns(base.ValidationWarning, match=warn_msg):
            self.type.validate()


class Test_FilePatterns:
    def setup_method(self):
        self.set = base.FilePatterns()

    def test_to_string(self):
        cond = base.Conditions()
        cond["flag"] = "value"
        cond_text = cond.to_string()
        files = base.Files()
        files["src"] = "dst"
        files_text = files.to_string()
        self.set[cond] = files
        expected = textwrap.dedent(
            """\
                <conditionalFileInstalls>
                  <patterns>
                    <pattern>
{}
{}
                    </pattern>
                  </patterns>
                </conditionalFileInstalls>""".format(
                textwrap.indent(cond_text, "    " * 5 + "  "),
                textwrap.indent(files_text, "    " * 5 + "  "),
            )
        )
        assert self.set.to_string() == expected
