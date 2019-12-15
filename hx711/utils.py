# -*- coding: utf-8 -*-


from collections import UserDict


class MultiDict(UserDict):
    def __init__(self, *args, **kwargs):
        super(MultiDict, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        self.data.setdefault(key, list()).append(value)

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key):
        if key in self.data:
            return self.data[key][0]
        return super(MultiDict, self).__getitem__(key)

    def get_all(self, key):
        return super(MultiDict, self).__getitem__(key)


class BidirectionalMultiDict(MultiDict):
    def __init__(self, *args, **kwargs):
        self.inverse = MultiDict()
        super(BidirectionalMultiDict, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super(BidirectionalMultiDict, self).__setitem__(key, value)
        self.inverse[value] = key

    def __delitem__(self, key):
        if key in self.data:
            for d in self.get_all(key):
                self.inverse.data[d].remove(key)
                if len(self.inverse.data[d]) == 0:
                    del self.inverse.data[d]
        super(BidirectionalMultiDict, self).__delitem__(key)
