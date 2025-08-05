import weakref

class Trackable:
    _instances = {}

    def __init__(self):
        # Optionally, add self to the global instances on creation
        self.__class__.add(self)

    @classmethod
    def add(cls, obj):
        cls._instances[id(obj)] = weakref.ref(obj, lambda _: cls._instances.pop(id(obj), None))

    @classmethod
    def instances(cls):
        # Return live objects only
        return [ref() for ref in cls._instances.values() if ref() is not None]

    def __len__(self):
        return len(self.instances())
