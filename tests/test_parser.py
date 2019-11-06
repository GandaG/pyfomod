import textwrap
from pathlib import Path

from pyfomod import parser
from pyfomod.errors import ErrorID, ErrorKind

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


def test_tuple_parse():
    root = parser.parse(str(PACKAGE_PATH))
    tuple_root = parser.parse((str(INFO_PATH), str(CONF_PATH)))
    assert root.to_string() == tuple_root.to_string()
    assert root._info.to_string() == tuple_root._info.to_string()


def test_parse(tmp_path):
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
    errors = []
    root = parser.parse((None, str(conf_path)), errors=errors)
    expected = [
        {
            "kind": ErrorKind.ERROR,
            "elem": None,
            "id": ErrorID.INVALID_SYNTAX,
            "title": "XML Syntax Error",
            "msg": "Element 'moduleDependencies': This element is not expected. "
            "Expected is ( moduleName ).",
        },
        {
            "kind": ErrorKind.WARNING,
            "elem": None,
            "id": ErrorID.COMMENTS_PRESENT,
            "title": "XML Comments Present",
            "msg": "There are comments in the fomod, they will be ignored.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": root.conditions,
            "id": ErrorID.INVALID_ENUM,
            "title": "Invalid Condition Type Attribute",
            "msg": "Condition Type was set to 'invalid' in tag 'moduleDependencies' "
            "but can only be one of: 'And', 'Or'. "
            "It was set to default 'And'.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": None,
            "id": ErrorID.REQUIRED_ATTRIBUTE,
            "title": "Missing File Attribute",
            "msg": "The 'file' attribute on the 'fileDependency' "
            "tag is required. This tag will be skipped.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": None,
            "id": ErrorID.DEFAULT_ATTRIBUTE,
            "title": "Missing State Attribute",
            "msg": "The 'state' attribute on the 'fileDependency' "
            "tag is required. It was set to 'Active'.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": None,
            "id": ErrorID.INVALID_ENUM,
            "title": "Invalid File Type Attribute",
            "msg": "File Type was set to 'invalid' in tag 'fileDependency' "
            "but can only be one of: 'Active', 'Inactive', 'Missing'. "
            "It was set to default 'Active'.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": None,
            "id": ErrorID.REQUIRED_ATTRIBUTE,
            "title": "Missing Flag Attribute",
            "msg": "The 'flag' attribute on the 'flagDependency' "
            "tag is required. This tag will be skipped.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": None,
            "id": ErrorID.DEFAULT_ATTRIBUTE,
            "title": "Missing Value Attribute",
            "msg": "The 'value' attribute on the 'flagDependency' "
            "tag is required. It was set to ''.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": None,
            "id": ErrorID.REQUIRED_ATTRIBUTE,
            "title": "Missing Version Attribute",
            "msg": "The 'version' attribute on the 'gameDependency' "
            "tag is required. This tag will be skipped.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": None,
            "id": ErrorID.REQUIRED_ATTRIBUTE,
            "title": "Missing Source Attribute",
            "msg": "The 'source' attribute on the 'file' "
            "tag is required. This tag will be skipped.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": root.pages,
            "id": ErrorID.INVALID_ENUM,
            "title": "Invalid Order Attribute",
            "msg": "Order was set to 'invalid' in tag 'installSteps' "
            "but can only be one of: "
            "'Ascending', 'Descending', 'Explicit'. "
            "It was set to default 'Ascending'.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": root.pages[0],
            "id": ErrorID.DEFAULT_ATTRIBUTE,
            "title": "Missing Name Attribute",
            "msg": "The 'name' attribute on the 'installStep' "
            "tag is required. It was set to ''.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": root.pages[0][0],
            "id": ErrorID.DEFAULT_ATTRIBUTE,
            "title": "Missing Name Attribute",
            "msg": "The 'name' attribute on the 'group' tag "
            "is required. It was set to ''.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": root.pages[0][0],
            "id": ErrorID.DEFAULT_ATTRIBUTE,
            "title": "Missing Type Attribute",
            "msg": "The 'type' attribute on the 'group' "
            "tag is required. It was set to 'SelectAny'.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": root.pages[0][1],
            "id": ErrorID.INVALID_ENUM,
            "title": "Invalid Group Type Attribute",
            "msg": "Group Type was set to 'invalid' in tag 'group' "
            "but can only be one of: "
            "'SelectAny', 'SelectAll', 'SelectAtLeastOne', "
            "'SelectAtMostOne', 'SelectExactlyOne'. "
            "It was set to default 'SelectAny'.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": root.pages[0][1][0],
            "id": ErrorID.DEFAULT_ATTRIBUTE,
            "title": "Missing Name Attribute",
            "msg": "The 'name' attribute on the 'plugin' "
            "tag is required. It was set to ''.",
        },
        {
            "kind": ErrorKind.ERROR,
            "elem": None,
            "id": ErrorID.INVALID_ENUM,
            "title": "Invalid Order Attribute",
            "msg": "Order was set to 'invalid' in tag 'optionalFileGroups' "
            "but can only be one of: "
            "'Ascending', 'Descending', 'Explicit'. "
            "It was set to default 'Ascending'.",
        },
        {
            "kind": ErrorKind.NOTE,
            "elem": None,
            "id": ErrorID.MISSING_INFO,
            "title": "Missing Info XML",
            "msg": "Info.xml is missing from the fomod subfolder.",
        },
    ]
    for expect, actual in zip(expected, errors):
        assert expect["kind"] is actual.kind
        assert expect["elem"] is actual.elem
        assert expect["id"] is actual.id
        assert expect["title"] == actual.title
        assert expect["msg"] == actual.msg
