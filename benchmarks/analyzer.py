"""Analyze a 'real' feed.json some frequency tables that we can use to generate
something like it. You probably do not need to use this, a perfectly good
freqdata.py is already included.

NOTE: Run this with cpython and make sure simplejson has the _speedups.so
compiled.

    $ curl -o benchmarks/feed.json --compressed \
    'http://en.mochimedia.com/feeds/games?format=json'
    $ python benchmarks/analyzer.py > benchmarks/freqdata.py

"""
import time
import pprint
from collections import Counter, defaultdict

import simplejson

def classify_length(s):
    n = len(s)
    if n < 1:
        return (0, 1)
    elif n < 10:
        return (1, 10)
    elif n < 100:
        return (10, 100)
    elif n < 1000:
        return (100, 1000)
    return (1000, 5000)

def classify_char(c):
    if c < '\x1f':
        return (0x00, 0x20)
    elif c <= '\x7f':
        return (0x20, 0x80)
    elif c <= u'\ud7ff':
        return (0x80, 0xd800)
    elif c <= u'\uffff':
        # note that we skip over 0xd800-0xdbff
        # to avoid generating invalid surrogate codepoints
        return (0xdc00, 0x10000)
    return (0x10000, 0x110000)

NoneType = type(None)
class TypeNameRepr(object):
    __slots__ = ['type']
    def __init__(self, typ):
        self.type = typ

    def __repr__(self):
        if self.type is NoneType:
            return 'None'
        return self.type.__name__

    def __eq__(self, other):
        return isinstance(other, TypeNameRepr) and self.type == other.type

    def __hash__(self):
        return hash(self.type)

def dictify(d):
    if isinstance(d, dict) and type(d) is not dict:
        return dict((k, dictify(v)) for (k, v) in d.iteritems())
    return d

def classify_json(games):
    freq = defaultdict(Counter)
    types = {}
    def classify(k, v):
        typ = type(v)
        try:
            rtyp = types[typ]
        except KeyError:
            rtyp = types[typ] = TypeNameRepr(typ)
        if typ in (str, unicode, list):
            length = classify_length(v)
            rtyp = (rtyp, length)
            if typ in (str, unicode):
                subk = (k, rtyp)
                for c in v:
                    freq[subk][classify_char(c)] += 1
            else:
                subk = (k, rtyp)
                for subv in v:
                    classify(subk, subv)
        freq[k][rtyp] += 1
    for g in games:
        for k, v in g.iteritems():
            classify(k, v)
    return dictify(freq)

def main():
    d = simplejson.loads(open('benchmarks/feed.json', 'rb').read())
    return classify_json(d['games'])

if __name__ == '__main__':
    freq = main()
    print '# generated by analyzer.py on ' + time.ctime()
    print 'FREQ = ' + pprint.pformat(freq)
    print
