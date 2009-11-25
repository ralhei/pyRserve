# This file is autogenerated from /home/heinkel/Cellzome/pyRserve/pyRserve/test_rparser.py
# It contains the translation of r expressions into their 
# (network-) serialized representation.

binaryRExpressions = {
    '"abc"': '\x01\x00\x01\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x08\x00\x00\x22\x04\x00\x00\x61\x62\x63\x00',
    '1': '\x01\x00\x01\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x0c\x00\x00\x21\x08\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x3f',
    'as.integer(c(1))': '\x01\x00\x01\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x08\x00\x00\x20\x04\x00\x00\x01\x00\x00\x00',
    'c(1, 2)': '\x01\x00\x01\x00\x18\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x14\x00\x00\x21\x10\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x3f\x00\x00\x00\x00\x00\x00\x00\x40',
    'as.integer(c(1, 2))': '\x01\x00\x01\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x0c\x00\x00\x20\x08\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00',
    'c("abc", "defghi")': '\x01\x00\x01\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x10\x00\x00\x22\x0c\x00\x00\x61\x62\x63\x00\x64\x65\x66\x67\x68\x69\x00\x01',
    'seq(1, 5)': '\x01\x00\x01\x00\x1c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x18\x00\x00\x20\x14\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00',
    'list("otto", "gustav")': '\x01\x00\x01\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x1c\x00\x00\x10\x18\x00\x00\x22\x08\x00\x00\x6f\x74\x74\x6f\x00\x01\x01\x01\x22\x08\x00\x00\x67\x75\x73\x74\x61\x76\x00\x01',
    'list(husband="otto", wife="erna")': '\x01\x00\x01\x00\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x40\x00\x00\x90\x3c\x00\x00\x15\x20\x00\x00\x22\x10\x00\x00\x68\x75\x73\x62\x61\x6e\x64\x00\x77\x69\x66\x65\x00\x01\x01\x01\x13\x08\x00\x00\x6e\x61\x6d\x65\x73\x00\x00\x00\x22\x08\x00\x00\x6f\x74\x74\x6f\x00\x01\x01\x01\x22\x08\x00\x00\x65\x72\x6e\x61\x00\x01\x01\x01',
    'list(n="Fred", no_c=2, c_ages=c(4,7))': '\x01\x00\x01\x00\x58\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x54\x00\x00\x90\x50\x00\x00\x15\x20\x00\x00\x22\x10\x00\x00\x6e\x00\x6e\x6f\x5f\x63\x00\x63\x5f\x61\x67\x65\x73\x00\x01\x01\x13\x08\x00\x00\x6e\x61\x6d\x65\x73\x00\x00\x00\x22\x08\x00\x00\x46\x72\x65\x64\x00\x01\x01\x01\x21\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x21\x10\x00\x00\x00\x00\x00\x00\x00\x00\x10\x40\x00\x00\x00\x00\x00\x00\x1c\x40',
    }