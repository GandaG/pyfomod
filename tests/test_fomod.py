import textwrap
from collections import OrderedDict

from pyfomod import fomod


class TestBaseFomod:
    def test_write_attributes(self):
        attrib = {"boop": "beep", "value": "1"}
        expected = ' boop="beep" value="1"'
        assert fomod.BaseFomod._write_attributes(attrib) == expected

    def test_write_children(self):
        children = OrderedDict(
            [("first", ({}, "text")), ("second", ({"beep": "boop"}, ""))]
        )
        expected = '\n<first>text</first>\n<second beep="boop"/>'
        test = fomod.BaseFomod("", {})
        test._children = children
        assert test._write_children() == expected


class TestRoot:
    def setup_method(self):
        self.root = fomod.Root()

    def test_name(self):
        self.root.name = "beep"
        assert self.root.name == "beep"
        assert self.root._name.name == "beep"

    def test_image(self):
        self.root.image = "beep"
        assert self.root.image == "beep"
        assert self.root._image._attrib["path"] == "beep"

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
        test = fomod.Conditions()
        self.root.conditions = test
        assert self.root.conditions is test
        assert self.root._conditions is test
        assert test._tag == "moduleDependencies"

    def test_files(self):
        test = fomod.Files()
        self.root.files = test
        assert self.root.files is test
        assert self.root._files is test
        assert test._tag == "requiredInstallFiles"

    def test_pages(self):
        test = fomod.Pages()
        self.root.pages = test
        assert self.root.pages is test
        assert self.root._pages is test

    def test_file_patterns(self):
        test = fomod.FilePatterns()
        self.root.file_patterns = test
        assert self.root.file_patterns is test
        assert self.root._file_patterns is test

    def test_to_string(self):
        self.root.name = "Name"
        self.root.image = "path/to/image.png"
        expected = textwrap.dedent(
            """\
            <config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">
              <moduleName>Name</moduleName>
              <moduleImage path="path/to/image.png"/>
            </config>"""
        )
        assert self.root.to_string() == expected

    def test_validate(self):
        expected = fomod.ValidationWarning(
            "Empty Installer",
            "This fomod is empty, nothing will be installed.",
            self.root,
        )
        assert expected in self.root.validate()
        page = fomod.Page()
        page.conditions["boop"] = "beep"
        page.append(fomod.Group())
        self.root.pages.append(page)
        expected = fomod.ValidationWarning(
            "Impossible Flags",
            'The flag "boop" is never created or set.',
            page.conditions,
        )
        assert expected in self.root.validate()


class TestInfo:
    def setup_method(self):
        self.info = fomod.Info()

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


class TestName:
    def setup_method(self):
        self.name = fomod.Name()

    def test_to_string(self):
        self.name._attrib = {"first": "second"}
        self.name.name = "Name"
        expected = '<moduleName first="second">Name</moduleName>'
        assert self.name.to_string() == expected

    def test_validate(self):
        expected = fomod.ValidationWarning(
            "Missing Installer Name", "This fomod does not have a name.", self.name
        )
        assert expected in self.name.validate()


class TestImage:
    def setup_method(self):
        self.image = fomod.Image()

    def test_to_string(self):
        self.image._attrib = {"path": "path/to/image.png"}
        expected = '<moduleImage path="path/to/image.png"/>'
        assert self.image.to_string() == expected


class TestConditions:
    def setup_method(self):
        self.cond = fomod.Conditions()

    def test_type(self):
        self.cond.type = fomod.ConditionType.OR
        assert self.cond.type is fomod.ConditionType.OR
        assert self.cond._type is fomod.ConditionType.OR

    def test_to_string(self):
        self.cond.type = fomod.ConditionType.OR
        self.cond[None] = "1.0"
        self.cond["boop"] = "beep"
        nest = fomod.Conditions()
        nest.type = fomod.ConditionType.AND
        nest["file"] = fomod.FileType.MISSING
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
        assert self.cond.to_string() == expected

    def test_validate(self):
        expected = fomod.ValidationWarning(
            "Empty Conditions",
            "This element should have at least one condition present.",
            self.cond,
            critical=True,
        )
        assert expected in self.cond.validate()
        nest = fomod.Conditions()
        self.cond[nest] = None
        expected = fomod.ValidationWarning(
            "Empty Conditions",
            "This element should have at least one condition present.",
            nest,
            critical=True,
        )
        assert expected in self.cond.validate()
        self.cond[None] = ""
        expected = fomod.ValidationWarning(
            "Empty Version Dependency",
            "This version dependency is empty and may not work correctly.",
            self.cond,
        )
        assert expected in self.cond.validate()
        self.cond[""] = fomod.FileType.ACTIVE
        expected = fomod.ValidationWarning(
            "Empty File Dependency",
            "This file dependency depends on no file, may not work correctly.",
            self.cond,
        )
        assert expected in self.cond.validate()
        self.cond._tag = "moduleDependencies"
        self.cond["boop"] = "beep"
        expected = fomod.ValidationWarning(
            "Useless Flags",
            "Flag boop shouldn't be used here since it can't have been set.",
            self.cond,
        )
        assert expected in self.cond.validate()


class TestFiles:
    def setup_method(self):
        self.files = fomod.Files()

    def test_getitem(self):
        item1 = fomod.File("file")
        item1.src = "boop"
        item1.dst = "boopity"
        item2 = fomod.File("folder")
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
        item1 = fomod.File("file")
        item1.src = "boop"
        item1.dst = "boopity"
        item2 = fomod.File("folder")
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


class TestFile:
    def setup_method(self):
        self.file = fomod.File()

    def test_to_string(self):
        self.file._tag = "file"
        self.file.src = "src"
        self.file.dst = "dst"
        expected = '<file source="src" destination="dst"/>'
        assert self.file.to_string() == expected
        self.file.dst = ""
        expected = '<file source="src" destination=""/>'
        assert self.file.to_string() == expected
        self.file.dst = None
        expected = '<file source="src"/>'
        assert self.file.to_string() == expected

    def test_validate(self):
        expected = fomod.ValidationWarning(
            "Empty Source Field",
            "No source specified, this could lead to problems installing.",
            self.file,
            critical=True,
        )
        assert expected in self.file.validate()


class TestPages:
    def setup_method(self):
        self.pages = fomod.Pages()

    def test_order(self):
        self.pages.order = fomod.Order.EXPLICIT
        assert self.pages.order is fomod.Order.EXPLICIT
        assert self.pages._order is fomod.Order.EXPLICIT

    def test_to_string(self):
        page1 = fomod.Page()
        page1.append(fomod.Group())
        page1.name = "boop"
        text = page1.to_string()
        page2 = fomod.Page()
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


class TestPage:
    def setup_method(self):
        self.page = fomod.Page()

    def test_name(self):
        self.page.name = "boop"
        assert self.page.name == "boop"
        assert self.page._name == "boop"

    def test_conditions(self):
        test = fomod.Conditions()
        self.page.conditions = test
        assert self.page.conditions is test
        assert self.page._conditions is test

    def test_order(self):
        self.page.order = fomod.Order.EXPLICIT
        assert self.page.order is fomod.Order.EXPLICIT
        assert self.page._order is fomod.Order.EXPLICIT

    def test_to_string(self):
        group1 = fomod.Group()
        group1.append(fomod.Option())
        text = group1.to_string()
        group2 = fomod.Group()
        self.page.extend([group1, group2])
        self.page.name = "boop"
        self.page.order = fomod.Order.ASCENDING
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
        expected = fomod.ValidationWarning(
            "Empty Page Name", "This page has no name.", self.page
        )
        assert expected in self.page.validate()
        expected = fomod.ValidationWarning(
            "Empty Page", "This page is empty.", self.page
        )
        assert expected in self.page.validate()


class TestGroup:
    def setup_method(self):
        self.group = fomod.Group()

    def test_name(self):
        self.group.name = "boop"
        assert self.group.name == "boop"
        assert self.group._name == "boop"

    def test_order(self):
        self.group.order = fomod.Order.EXPLICIT
        assert self.group.order is fomod.Order.EXPLICIT
        assert self.group._order is fomod.Order.EXPLICIT

    def test_type(self):
        self.group.type = fomod.GroupType.ALL
        assert self.group.type is fomod.GroupType.ALL
        assert self.group._type is fomod.GroupType.ALL

    def test_to_string(self):
        option1 = fomod.Option()
        option1_text = option1.to_string()
        self.group.append(option1)
        self.group.name = "name"
        self.group.order = fomod.Order.DESCENDING
        self.group.type = fomod.GroupType.ALL
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
        expected = fomod.ValidationWarning(
            "Empty Group", "This group is empty.", self.group
        )
        assert expected in self.group.validate()
        expected = fomod.ValidationWarning(
            "Empty Group Name", "This group has no name.", self.group
        )
        assert expected in self.group.validate()

        self.group.type = fomod.GroupType.ATLEASTONE
        expected = fomod.ValidationWarning(
            "Not Enough Selectable Options",
            "This group needs at least one selectable "
            "option but none are available.",
            self.group,
            critical=True,
        )
        assert expected in self.group.validate()

        self.group.type = fomod.GroupType.EXACTLYONE
        expected = fomod.ValidationWarning(
            "Not Enough Selectable Options",
            "This group needs exactly one selectable " "option but none are available.",
            self.group,
            critical=True,
        )
        assert expected in self.group.validate()

        option1 = fomod.Option()
        option1.type = fomod.OptionType.REQUIRED
        self.group.append(option1)
        option2 = fomod.Option()
        option2.type = fomod.OptionType.REQUIRED
        self.group.append(option2)

        self.group.type = fomod.GroupType.ATMOSTONE
        expected = fomod.ValidationWarning(
            "Too Many Required Options",
            "This group can have one option selected "
            "at most but at least two are required.",
            self.group,
            critical=True,
        )
        assert expected in self.group.validate()

        self.group.type = fomod.GroupType.EXACTLYONE
        expected = fomod.ValidationWarning(
            "Too Many Required Options",
            "This group can only have exactly one "
            "option selected but at least two are required.",
            self.group,
            critical=True,
        )
        assert expected in self.group.validate()


class TestOption:
    def setup_method(self):
        self.option = fomod.Option()

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
        test = fomod.Files()
        self.option.files = test
        assert self.option.files is test
        assert self.option._files is test

    def test_flags(self):
        test = fomod.Flags()
        self.option.flags = test
        assert self.option.flags is test
        assert self.option._flags is test

    def test_type(self):
        self.option.type = fomod.OptionType.REQUIRED
        assert self.option.type is fomod.OptionType.REQUIRED
        assert self.option._type is fomod.OptionType.REQUIRED
        test = fomod.Type()
        self.option.type = test
        assert self.option.type is test
        assert self.option._type is test

    def test_to_string(self):
        self.option.name = "boo"
        self.option.description = "bee"
        self.option.image = "path"
        self.option.type = fomod.OptionType.RECOMMENDED
        files = fomod.Files()
        files["src"] = "dst"
        files_text = files.to_string()
        self.option.files = files
        flags = fomod.Flags()
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
        expected = [
            fomod.ValidationWarning(
                "Empty Option Name", "This option has no name.", self.option
            ),
            fomod.ValidationWarning(
                "Empty Option Description",
                "This option has no description.",
                self.option,
            ),
            fomod.ValidationWarning(
                "Option Does Nothing",
                "This option installs no files and sets no flags.",
                self.option,
            ),
        ]
        assert self.option.validate() == expected


class TestFlags:
    def setup_method(self):
        self.flags = fomod.Flags()

    def test_to_string(self):
        self.flags["flag"] = "value"
        expected = textwrap.dedent(
            """\
                <conditionFlags>
                  <flag name="flag">value</flag>
                </conditionFlags>"""
        )
        assert self.flags.to_string() == expected


class TestType:
    def setup_method(self):
        self.type = fomod.Type()

    def test_default(self):
        self.type.default = fomod.OptionType.RECOMMENDED
        assert self.type.default is fomod.OptionType.RECOMMENDED
        assert self.type._default is fomod.OptionType.RECOMMENDED

    def test_to_string(self):
        self.type.default = fomod.OptionType.REQUIRED
        cond = fomod.Conditions()
        cond["flag"] = "value"
        self.type[cond] = fomod.OptionType.RECOMMENDED
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
        expected = fomod.ValidationWarning(
            "Empty Type Descriptor",
            "This type descriptor is empty and will never set a type.",
            self.type,
            critical=True,
        )
        assert expected in self.type.validate()


class TestFilePatterns:
    def setup_method(self):
        self.set = fomod.FilePatterns()

    def test_to_string(self):
        cond = fomod.Conditions()
        cond["flag"] = "value"
        cond_text = cond.to_string()
        files = fomod.Files()
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
