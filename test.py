from btree import *
import random


# BTree Testing 

sizes   = [1, 2, 3, 4, 5, 12, 25, 100, 1000]
ds      = [2, 3, 4, 5, 6, 7, 8, 9, 10]
randmin = -1000
randmax = 1000

def testiter(d, size):
    items = [random.randint(randmin, randmax) for i in range(size)]
    random.shuffle(items)
    insertorder = items[:]
    random.shuffle(items)
    deleteorder = items[:]
    t = BTree(d, lambda x: x)
    for i in insertorder:
        t.insert(i)
        t.validate()
    for i in deleteorder:
        t.delete(i)
        t.validate()

def test(iters = 1):
    for i in range(iters):
        random.shuffle(sizes)
        random.shuffle(ds)
        pairs = zip(ds, sizes)
        for p in pairs:
            testiter(*p)
    print "Success! No errors found."
