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
            </config>"""
    )
    (tmp_path / "fomod").mkdir()
    conf_path = tmp_path / "fomod" / "moduleconfig.xml"
    with conf_path.open("w") as conf_file:
        conf_file.write(content)
        conf_file.write("\n")
    expected = [
        fomod.ValidationWarning(
            "Syntax Error",
            "Element 'config': Missing child element(s). "
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
            "Missing Info",
            "Info.xml is missing from the fomod subfolder.",
            None,
            critical=True,
        ),
    ]
    warnings = []
    parser.parse((None, str(conf_path)), warnings=warnings)
    assert warnings == expected
