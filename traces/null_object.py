class NullObject(object):
    def __bool__(self):
        return False

nan = NullObject()
