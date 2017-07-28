import os

from lxml import etree

import pytest
from pyfomod import parser


class Test_Lookup:
    def test_base_class(self, single_parse):
        for tree in single_parse:
            for element in tree.iter(tag=etree.Element):
                assert isinstance(element, parser.FomodElement)

    def test_subclasses(self, single_parse):
        root = single_parse[1]
        assert isinstance(root, parser.Root)
        mod_dep = root.findall('.//moduleDependencies')
        assert(all(isinstance(elem, parser.Dependencies)) for elem in mod_dep)
        dep = root.findall('.//dependencies')
        assert(all(isinstance(elem, parser.Dependencies)) for elem in dep)
        vis = root.findall('.//visible')
        assert(all(isinstance(elem, parser.Dependencies)) for elem in vis)
        step = root.findall('.//installStep')
        assert(all(isinstance(elem, parser.InstallStep)) for elem in step)
        group = root.findall('.//group')
        assert(all(isinstance(elem, parser.Group)) for elem in group)
        plugin = root.findall('.//plugin')
        assert(all(isinstance(elem, parser.Plugin)) for elem in plugin)
        tp_dep = root.findall('.//dependencyType')
        assert(all(isinstance(elem, parser.TypeDependency)) for elem in tp_dep)
        tp_pat = root.findall('.//pattern/type')
        assert(all(isinstance(elem, parser.TypePattern)) for elem in tp_pat)
        fl_pat = root.findall('.//pattern/files')
        assert(all(isinstance(elem, parser.InstallPattern)) for elem in fl_pat)


class Test_Validate_Installer:
    def test_root(self):
        with pytest.raises(NotImplementedError):
            parser.validate_installer(parser.Root())

    def test_tuple(self, single_parse):
        assert parser.validate_installer(tuple(single_parse))

    def test_list(self, single_parse):
        assert parser.validate_installer(list(single_parse))

    def test_path(self, valid_fomod):
        assert parser.validate_installer(valid_fomod)
        assert parser.validate_installer(os.path.join(valid_fomod, 'fomod'))

    def test_invalid_arg(self, tmpdir):
        with pytest.raises(ValueError):
            parser.validate_installer(str(tmpdir))
