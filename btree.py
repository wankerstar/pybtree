# BTree.py - Python B-Tree implementation
# Copyright 2012 Tristan Ankerstar, Licensed under GPL.

class BTreeException(Exception):
    pass

class BNode:
    def __init__(self):
        self.items      = []
        self.children   = []

    def find_by_key(self, key, keyfunc, selfcheck=False):
        """Returns an index and a bool, reperesenting 'child found here.'
           Bool ise true only if selfcheck is enabled (deletion case),
           in which case the index represents the item to delete.
           Otherwise, it's the child to check."""
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
        """Merges this node with othernode, its right neighbor. Merge
            propogates down the tree, resulting in a bubble if overflow."""
        self.items += othernode.items
        if not self.children == []:
            l_children = self.children
            l_child = l_children.pop(-1)
            r_children = othernode.children
            r_child = r_children.pop(0)
            bubble = l_child.merge(r_child, keyfunc, maxcount)
            if bubble is None:  # Easy case, nodes below are ok
                self.children = l_children + [l_child] + r_children
            else:               # Overflow below
                self.children = l_children + l_child.split() + r_children
                return self.insert_here(bubble, keyfunc, maxcount)
        if len(self.items) > maxcount:
            return self.pop_median()

    def delete(self, key, keyfunc, mincount, maxcount):
        """Returns True if underflow, False otherwise."""
        # First, check if the item is here, and get the index of the item
        #   or the child to check.
        (here, ind) = self.find_by_key(key, keyfunc, selfcheck=True)
        if self.children == []:   # We're a leaf
            if here:    # Item is here - kill it, merging will be handled above.
                del self.items[ind]
                return len(self.items) < mincount
            else:       # Whoopsie.
                raise BTreeException("Item not in tree.")
        l_children = self.children[:ind]
        r_children = self.children[ind:]
        # Figure out which children to merge and which item guards them. 
        if len(r_children) == 1:
            l_child     = l_children.pop(-1)
            deadchild   = r_children.pop(0)
            item_ind    = ind - 1      # The item list is shorter than the childlist
        else:
            l_child     = r_children.pop(0)
            deadchild   = r_children.pop(0)
            item_ind    = ind
        # Okay, now we can work.
        if here:   # It's here!
            del self.items[ind]
            bubble = l_child.merge(deadchild, keyfunc, maxcount)
            if not bubble is None:  # Great, we don't even change size.
                self.children = l_children + l_child.split() + r_children
                self.insert_here(bubble, keyfunc, maxcount)
                return False
            else:
                self.children = l_children + [l_child] + r_children
                return len(self.items) < mincount   # Have to check for underflow
        else:
            exp_child = self.children[ind]
            underflow = exp_child.delete(key, keyfunc, mincount, maxcount)
            if underflow:
                # Need to merge the underflow node with a neighbor. 
                bubble = l_child.merge(deadchild, keyfunc, maxcount)
                if not bubble is None:  # Merge caused overflow.
                    self.children = l_children + l_child.split() + r_children
                    # Replace the decision item with the new median, push.
                    item                    = self.items[item_ind]
                    self.items[item_ind]    = bubble
                    self.insert(item, keyfunc, maxcount)
                    # Split made room, so there can be no bubble.
                    return False
                else:
                    # Fewer children now, must try to push an item down.
                    item = self.items.pop(item_ind)
                    bubble = l_child.insert(item, keyfunc, maxcount)
                    if bubble is None:
                        self.children = l_children + [l_child] + r_children
                        return len(self.items) < mincount   # Underflow possible
                    else:
                        self.children = l_children + l_child.split() + r_children
                        self.insert_here(bubble, keyfunc, maxcount)
                        return False
            else:
                return False
      
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
    """BTree class. Takes a max nodesize (min will be integer max div 2)
        and a key function which is used to determine ordering. Naturally,
        elements must be of a time such that keyfunc produces an ordering.
       Supports iteration, insertion, and deletion."""
    def __init__(self, maxsize, keyfunc):
        self.root    = BNode()
        self.maxsize = int(maxsize)
        self.minsize = self.maxsize / 2
        self.keyfunc = keyfunc

    def _mk_new_root(self, item):
        newroot             = BNode()
        newroot.add_item(item, self.keyfunc)
        newroot.children    = self.root.split()
        self.root           = newroot

    def _delete(self, key):
        self.root.delete(key, self.keyfunc, self.minsize, self.maxsize)
        if self.root.items == []:
            if not self.root.children == []:
                self.root = self.root.children[0]

    def insert(self, item):
        bubble = self.root.insert(item, self.keyfunc, self.maxsize)
        if not bubble is None:
            self._mk_new_root(bubble)

    def delete(self, item):
        self._delete(self.keyfunc(item))

    def delete_by_key(self, key):
        self._delete(key)

    def __iter__(self):
        return self.root.__iter__()

    # Debugging / test code follows
    def validate(self):
        if not self._val_size(self.root, ignoremin=True):
            raise BTreeException("Size validation error!")
        if not self._val_order():
            raise BTreeException("Order validation error!")

    def _val_size(self, node, ignoremin=False):
        size = len(node.items)
        if not ignoremin and size < self.minsize:
            return False
        return size <= self.maxsize and len(node.children) in (0, size+1) and \
                all(map(self._val_size, node.children))

    def _val_order(self):
        isordered = lambda x, y: self.keyfunc(x) <= self.keyfunc(y)
        prev = None
        for i in self:
            if not isordered(prev, i):
                return False
            prev = i
        return True
