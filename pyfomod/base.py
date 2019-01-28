# Copyright 2016 Daniel Nunes
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

"""Base classes."""

from collections.abc import ItemsView, KeysView, Mapping, ValuesView


class HashableSequence(object):
    def __getitem__(self, key):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __delitem__(self, key):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def insert(self, index, value):
        raise NotImplementedError

    def __iter__(self):
        i = 0
        try:
            while True:
                v = self[i]
                yield v
                i += 1
        except IndexError:
            return

    def __contains__(self, value):
        for v in self:
            if v is value or v == value:
                return True
        return False

    def __reversed__(self):
        for i in reversed(range(len(self))):
            yield self[i]

    def index(self, value, start=0, stop=None):
        if start is not None and start < 0:
            start = max(len(self) + start, 0)
        if stop is not None and stop < 0:
            stop += len(self)

        i = start
        while stop is None or i < stop:
            try:
                v = self[i]
                if v is value or v == value:
                    return i
            except IndexError:
                break
            i += 1
        raise ValueError

    def count(self, value):
        return sum(1 for v in self if v is value or v == value)

    def append(self, value):
        self.insert(len(self), value)

    def clear(self):
        try:
            while True:
                self.pop()
        except IndexError:
            pass

    def reverse(self):
        n = len(self)
        for i in range(n // 2):
            self[i], self[n - i - 1] = self[n - i - 1], self[i]

    def extend(self, values):
        if values is self:
            values = list(values)
        for v in values:
            self.append(v)

    def pop(self, index=-1):
        v = self[index]
        del self[index]
        return v

    def remove(self, value):
        del self[self.index(value)]

    def __iadd__(self, values):
        self.extend(values)
        return self


class HashableMapping(object):
    def __getitem__(self, key):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __delitem__(self, key):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def keys(self):
        return KeysView(self)

    def items(self):
        return ItemsView(self)

    def values(self):
        return ValuesView(self)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    __marker = object()

    def pop(self, key, default=__marker):
        try:
            value = self[key]
        except KeyError:
            if default is self.__marker:
                raise
            return default
        else:
            del self[key]
            return value

    def popitem(self):
        try:
            key = next(iter(self))
        except StopIteration:
            raise KeyError from None
        value = self[key]
        del self[key]
        return key, value

    def clear(self):
        try:
            while True:
                self.popitem()
        except KeyError:
            pass

    def update(*args, **kwargs):
        if not args:
            raise TypeError(
                "descriptor 'update' of 'HashableMapping' object needs an argument"
            )
        self, *args = args
        if len(args) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(args))
        if args:
            other = args[0]
            if isinstance(other, Mapping):
                for key in other:
                    self[key] = other[key]
            elif hasattr(other, "keys"):
                for key in other.keys():
                    self[key] = other[key]
            else:
                for key, value in other:
                    self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default
