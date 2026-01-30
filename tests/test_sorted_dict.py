from traces.sorted_dict import SortedDict


def test_insert_maintains_sorted_order():
    d = SortedDict()
    d[3] = "c"
    d[1] = "a"
    d[2] = "b"
    assert d.keys() == [1, 2, 3]
    assert d.values() == ["a", "b", "c"]
    assert d.items() == [(1, "a"), (2, "b"), (3, "c")]


def test_overwrite_does_not_duplicate_key():
    d = SortedDict()
    d[1] = "a"
    d[1] = "b"
    assert d.keys() == [1]
    assert d[1] == "b"
    assert len(d) == 1


def test_delete():
    d = SortedDict({1: "a", 2: "b", 3: "c"})
    del d[2]
    assert d.keys() == [1, 3]
    assert 2 not in d
    assert len(d) == 2


def test_update_from_dict():
    d = SortedDict()
    d[5] = "e"
    d.update({1: "a", 3: "c"})
    assert d.keys() == [1, 3, 5]


def test_update_from_sorted_dict():
    a = SortedDict({1: "a", 3: "c"})
    b = SortedDict({2: "b"})
    b.update(a)
    assert b.keys() == [1, 2, 3]


def test_update_from_pairs():
    d = SortedDict()
    d.update([(3, "c"), (1, "a")])
    assert d.keys() == [1, 3]


def test_init_from_dict():
    d = SortedDict({3: "c", 1: "a", 2: "b"})
    assert d.keys() == [1, 2, 3]


def test_peekitem():
    d = SortedDict({1: "a", 2: "b", 3: "c"})
    assert d.peekitem() == (3, "c")
    assert d.peekitem(0) == (1, "a")
    assert d.peekitem(-2) == (2, "b")


def test_bisect():
    d = SortedDict({10: "a", 20: "b", 30: "c"})
    assert d.bisect_left(20) == 1
    assert d.bisect_right(20) == 2
    assert d.bisect_left(15) == 1
    assert d.bisect_right(15) == 1


def test_irange_inclusive():
    d = SortedDict({1: "a", 2: "b", 3: "c", 4: "d", 5: "e"})
    assert list(d.irange(2, 4)) == [2, 3, 4]
    assert list(d.irange(2, 4, inclusive=(False, False))) == [3]
    assert list(d.irange(2, 4, inclusive=(True, False))) == [2, 3]
    assert list(d.irange(2, 4, inclusive=(False, True))) == [3, 4]


def test_delete_range():
    d = SortedDict({1: "a", 2: "b", 3: "c", 4: "d", 5: "e"})
    d.delete_range(2, 4)
    assert d.keys() == [1, 5]
    assert len(d) == 2


def test_delete_range_exclusive():
    d = SortedDict({1: "a", 2: "b", 3: "c", 4: "d", 5: "e"})
    d.delete_range(2, 4, inclusive=(False, False))
    assert d.keys() == [1, 2, 4, 5]


def test_islice():
    d = SortedDict({1: "a", 2: "b", 3: "c", 4: "d"})
    assert list(d.islice(1, 3)) == [2, 3]
    assert list(d.islice(None, 2)) == [1, 2]


def test_empty():
    d = SortedDict()
    assert len(d) == 0
    assert not d
    assert d.keys() == []
    assert list(d) == []


def test_bool():
    d = SortedDict()
    assert not d
    d[1] = "a"
    assert d


def test_eq():
    a = SortedDict({1: "a", 2: "b"})
    b = SortedDict({2: "b", 1: "a"})
    assert a == b


def test_repr():
    d = SortedDict({2: "b", 1: "a"})
    assert repr(d) == "SortedDict({1: 'a', 2: 'b'})"
