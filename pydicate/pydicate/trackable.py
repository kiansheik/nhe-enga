import weakref
import inspect


class Trackable:
    _instances = {}

    def __init__(self):
        self._var_name = self.get_var_name_from_stack()
        self.__class__.add(self)

    @classmethod
    def add(cls, obj):
        cls._instances[id(obj)] = weakref.ref(
            obj, lambda _: cls._instances.pop(id(obj), None)
        )

    @classmethod
    def instances(cls):
        # Return live objects only
        return [ref() for ref in cls._instances.values() if ref() is not None]

    def get_var_name_from_stack(self):
        for frame_info in inspect.stack():
            frame = frame_info.frame
            for var_name, var_val in frame.f_globals.items():
                if var_val is self:
                    return var_name
        return None

    @property
    def var_name(self):
        if self._var_name:
            return self._var_name
        self._var_name = self.get_var_name_from_stack()
        return self._var_name
