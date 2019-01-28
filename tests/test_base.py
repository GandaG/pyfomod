from pyfomod import base


class TestHashableSequence:
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


class TestHashableMapping:
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
