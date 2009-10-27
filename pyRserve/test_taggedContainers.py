
# unittests for classes from taggedContainers

from taggedContainers import TaggedList

def test_TaggedList_init_emtpy():
    t = TaggedList()
    assert t.astuples == []
    assert len(t) == 0

def test_TaggedList_init_one_value():
    t = TaggedList([11])
    assert t.astuples == [(None, 11)]
    assert len(t) == 1
    assert t[0] == 11

def test_TaggedList_init_one_value_with_key():
    t = TaggedList([('v1', 11)])
    assert t.astuples == [('v1', 11)]
    assert len(t) == 1
    assert t[0] == 11
    assert t['v1'] == 11

def test_TaggedList_init_two_values_second_with_key():
    t = TaggedList([11, ('v2', 22)])
    assert t.astuples == [(None, 11), ('v2', 22)]
    assert len(t) == 2
    assert t[0] == 11
    assert t[1] == 22
    assert t['v2'] == 22

def test_TaggedList_append():
    t = TaggedList([11, ('v2', 22)])
    t.append(33)
    assert len(t) == 3
    assert t.values == [11, 22, 33]

def test_TaggedList_append_with_key():
    t = TaggedList([11, ('v2', 22)])
    t.append(v3=33)
    assert len(t) == 3
    assert t.values == [11, 22, 33]
    assert t['v3'] == 33
