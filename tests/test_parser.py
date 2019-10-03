import textwrap
from pathlib import Path

from pyfomod import fomod, parser

PACKAGE_PATH = Path(__file__).parent / "package_test"
INFO_PATH = Path(PACKAGE_PATH, "fomod", "info.xml")
CONF_PATH = Path(PACKAGE_PATH, "fomod", "moduleconfig.xml")


def test_preserve_data(tmp_path):
    with INFO_PATH.open() as info_file:
        orig_info = info_file.read()
    with CONF_PATH.open() as conf_file:
        orig_conf = conf_file.read()
    root = parser.parse(str(PACKAGE_PATH))
    parser.write(root, str(tmp_path))
    info_path = tmp_path / "fomod" / "info.xml"
    with info_path.open() as info_file:
        new_info = info_file.read()
    conf_path = tmp_path / "fomod" / "moduleconfig.xml"
    with conf_path.open() as conf_file:
        new_conf = conf_file.read()
    assert orig_info == new_info
    assert orig_conf == new_conf


def test_parse(tmp_path):
    root = parser.parse(str(PACKAGE_PATH))
    tuple_root = parser.parse((str(INFO_PATH), str(CONF_PATH)))
    assert root.to_string() == tuple_root.to_string()
    assert root._info.to_string() == tuple_root._info.to_string()
    content = textwrap.dedent(
        """\
            <config>
            <!-- comment -->
            <moduleDependencies operator="invalid">
                <fileDependency/>
                <fileDependency file=""/>
                <fileDependency file="" state="invalid"/>
                <flagDependency/>
                <flagDependency flag=""/>
                <gameDependency/>
            </moduleDependencies>
            <requiredInstallFiles>
                <file/>
            </requiredInstallFiles>
            <installSteps order="invalid">
                <installStep>
                    <optionalFileGroups order="invalid">
                        <group/>
                        <group name="something" type="invalid">
                            <plugins>
                                <plugin/>
                            </plugins>
                        </group>
                    </optionalFileGroups>
                </installStep>
            </installSteps>
            </config>
        """
    )
    (tmp_path / "fomod").mkdir()
    conf_path = tmp_path / "fomod" / "moduleconfig.xml"
    with conf_path.open("w") as conf_file:
        conf_file.write(content)
        conf_file.write("\n")
    warnings = []
    root = parser.parse((None, str(conf_path)), warnings=warnings)
    expected = [
        fomod.ValidationWarning(
            "Syntax Error",
            "Element 'moduleDependencies': This element is not expected. "
            "Expected is ( moduleName ).",
            None,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Comment Detected",
            "There are comments in this fomod, they will be ignored.",
            None,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Invalid Condition Type",
            "Condition Type was set to 'invalid' in tag 'moduleDependencies' "
            "but can only be one of: 'And', 'Or'. "
            "It was set to default 'And'.",
            root.conditions,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing File Attribute",
            "The 'file' attribute on the 'fileDependency' "
            "tag is required. This tag will be skipped.",
            None,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing State Attribute",
            "The 'state' attribute on the 'fileDependency' "
            "tag is required. It was set to 'Active'.",
            None,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Invalid File Type",
            "File Type was set to 'invalid' in tag 'fileDependency' "
            "but can only be one of: 'Missing', 'Inactive', 'Active'. "
            "It was set to default 'Active'.",
            None,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing Flag Attribute",
            "The 'flag' attribute on the 'flagDependency' "
            "tag is required. This tag will be skipped.",
            None,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing Value Attribute",
            "The 'value' attribute on the 'flagDependency' "
            "tag is required. It was set to ''.",
            None,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing Version Attribute",
            "The 'version' attribute on the 'gameDependency' "
            "tag is required. This tag will be skipped.",
            None,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing Source Attribute",
            "The 'source' attribute on the 'file' "
            "tag is required. This tag will be skipped.",
            None,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Invalid Order",
            "Order was set to 'invalid' in tag 'installSteps' "
            "but can only be one of: "
            "'Ascending', 'Descending', 'Explicit'. "
            "It was set to default 'Ascending'.",
            root.pages,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing Name Attribute",
            "The 'name' attribute on the 'installStep' "
            "tag is required. It was set to ''.",
            root.pages[0],
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing Name Attribute",
            "The 'name' attribute on the 'group' tag is required. It was set to ''.",
            root.pages[0][0],
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing Type Attribute",
            "The 'type' attribute on the 'group' "
            "tag is required. It was set to 'SelectAny'.",
            root.pages[0][0],
            critical=True,
        ),
        fomod.ValidationWarning(
            "Invalid Group Type",
            "Group Type was set to 'invalid' in tag 'group' "
            "but can only be one of: "
            "'SelectAtLeastOne', 'SelectAtMostOne', "
            "'SelectExactlyOne', 'SelectAll', 'SelectAny'. "
            "It was set to default 'SelectAny'.",
            root.pages[0][1],
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing Name Attribute",
            "The 'name' attribute on the 'plugin' "
            "tag is required. It was set to ''.",
            root.pages[0][1][0],
            critical=True,
        ),
        fomod.ValidationWarning(
            "Invalid Order",
            "Order was set to 'invalid' in tag 'optionalFileGroups' "
            "but can only be one of: "
            "'Ascending', 'Descending', 'Explicit'. "
            "It was set to default 'Ascending'.",
            None,
            critical=True,
        ),
        fomod.ValidationWarning(
            "Missing Info",
            "Info.xml is missing from the fomod subfolder.",
            None,
            critical=True,
        ),
    ]
    assert warnings == expected
