class BTreeException(Exception):
    pass

class BNode:
    def __init__(self):
        self.items      = []
        self.children   = []

    def find_by_key(self, key, keyfunc, selfcheck=False):
        """Returns index of appropriate child and a bool, reperesenting 'child found here.'
            Will be true only if selfcheck is enabled."""
        child_ind = None
        for ind, myitem in enumerate(self.items):
            mykey = keyfunc(myitem)
            if selfcheck and mykey == key:
                return (True, ind)   # Indicates item is at THIS node
            elif key < mykey:
                child_ind = ind
                break
        if child_ind is None:
            child_ind = ind + 1
        return (False, child_ind)

    def merge(self, othernode, keyfunc, maxcount):
        """Merges this node with othernode, its right neighbor."""
        self.items += othernode.items
        if not self.children == []:
            l_children = self.children[:]
            l_child = l_children.pop(-1)
            r_children = othernode.children[:]
            r_child = r_children.pop(0)
            bubble = l_child.merge(r_child, keyfunc, maxcount)
            if bubble is None:  # Easy case, nodes below are ok
                self.children = l_children + l_child + r_children
            else:               # Overflow below
                newkids = l_child.split()
                self.children = l_children + newkids + r_children
                return self.insert_here(bubble, keyfunc, maxcount)
        if len(self.items) > maxcount:
            return self.pop_median()

    def delete(self, key, keyfunc, mincount, maxcount):
        """Returns True if underflow, False otherwise."""
        (here, ind) = self.find_by_key(key, keyfunc, selfcheck=True)
        size = len(self.children)
        if size == 0:
            if here:
                del self.items[ind]
                return len(self.items) < mincount
            else:
                raise BTreeException("Item not in tree.")
        l_children = self.children[:ind]
        r_children = self.children[ind:]
        exp_child  = self.children[ind]  # This will be either the left or dead child
        if (not here) and len(r_children) == 1:    # End of childlist, may need to merge left
            l_child     = l_children.pop(-1)
            deadchild   = r_children.pop(0)
            item_ind    = ind - 1      # The item list is shorter than the childlist
        else:
            l_child     = r_children.pop(0)
            deadchild   = r_children.pop(0)
            item_ind    = ind
        if here:   # It's here!
            del self.items[ind]
            if self.children != []:
                bubble = l_child.merge(deadchild, keyfunc, maxcount)
                if not bubble is None:  # Great, we don't even change size.
                    self.children = l_children + l_child.split() + r_children
                    self.insert_here(bubble, keyfunc, maxcount)
                    return False
                else:
                    self.children = l_children + [l_child] + r_children
                    return len(self.items) < mincount   # Have to check for underflow
        else:
            underflow = exp_child.delete(key, keyfunc, mincount, maxcount)
            if underflow:
                # Hard stuff. Merge with a sibling, kill sibling.
                bubble = l_child.merge(deadchild, keyfunc, maxcount)
                if bubble is not None:  # Good, split below and we're happy
                    self.insert_here(bubble, keyfunc, maxcount)
                    self.children = l_children + [l_child] + r_children
                else:                   # One item too many, push it down
                    item = self.items.pop(item_ind)
                    bubble = l_child.insert(item, keyfunc, maxcount)
                    if bubble is None:
                        self.children = l_children + [l_child] + r_children
                    else:
                        self.children = l_children + l_child.split() + r_children
                        self.insert_here(bubble, keyfunc, maxcount)
                        return False
                    return len(self.items) < mincount   # May underflow
      
    def insert(self, item, keyfunc, maxcount):
        """Updates self, returns bubble-up item or None."""
        if self.children == []:
            return self.insert_here(item, keyfunc, maxcount)
        else:
            child_ind   = self.find_by_key(keyfunc(item), keyfunc)[1]
            child       = self.children[child_ind]
            bubble      = child.insert(item, keyfunc, maxcount)
            if not bubble is None:
                self.children = self.children[:child_ind] + child.split() + self.children[child_ind+1:]
                return self.insert_here(bubble, keyfunc, maxcount)

    def insert_here(self, item, keyfunc, maxcount):
        self.add_item(item, keyfunc)
        if len(self.items) > maxcount:
            return self.pop_median()
        else:
            return None

    def split(self):
        size = len(self.items)
        itemlists = (self.items[:size/2], self.items[size/2:])
        numkids = size + 2 # if we're splitting, we'd better have this many or 0
        childlists = (self.children[:numkids/2], self.children[numkids/2:])
        
        newnode = BNode()
        for (iternode, ind) in zip([self, newnode], [0, 1]):
            iternode.items = itemlists[ind]
            iternode.children = childlists[ind]
        return [self, newnode]

    def add_item(self, item, keyfunc):
        self.items.append(item)
        self.items.sort(key=keyfunc)
        # insertion is O(n), sorting O(log(n)) - we could do better

    def pop_median(self):
        size = len(self.items)
        midpoint = (size / 2) if size % 2 != 0 else (size-1)/2
        return self.items.pop(midpoint)

    def __iter__(self):
        if self.children == []:
            for i in self.items:
                yield i
        else:
            for thing in self.children[0]:
                yield thing 
            for i, c in zip(self.items, self.children[1:]):
                yield i
                for thing in c:
                    yield thing

class BTree:
    def __init__(self, minsize, maxsize, keyfunc):
        self.root    = BNode()
        self.minsize = minsize
        self.maxsize = maxsize
        self.keyfunc = keyfunc

    def _mk_new_root(self, item, keyfunc):
        newroot             = BNode()
        newroot.add_item(item, keyfunc)
        newroot.children    = self.root.split()
        self.root           = newroot

    def insert(self, item):
        bubble = self.root.insert(item, self.keyfunc, self.maxsize)
        if not bubble is None:
            self._mk_new_root(bubble, self.keyfunc)

    def delete(self, item):
        self.root.delete(item, self.keyfunc, self.minsize, self.maxsize)
        if self.root.items == []:
            if not self.root.children == []:
                self.root = self.root.children[0]

    def __iter__(self):
        return self.root.__iter__()

def verify(t):
    l = None
    for x in t:
        if l > x:
            print "SHIT"
        l = x

def test():
    t = BTree(2,4, lambda x:x)
    for i in range(18):
        t.insert(i)
    for d in [12, 11, 3, 9, 1, 8, 4, 13]:
        t.delete(d)
        verify(t)
    return t
