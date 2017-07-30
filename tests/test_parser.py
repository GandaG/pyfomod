from lxml import etree

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
