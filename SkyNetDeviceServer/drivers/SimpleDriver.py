from FieldInfo import FieldInfo
from twisted.internet import defer


class SimpleDriver:
    def __init__(self, updated):
        self.updated = updated

    def get_device_fields(self):
        return defer.maybeDeferred({})

    def update_device_field(self, field_name, value):
        def callb(res):
            for field in self.fields:
                if field.Writable and field.Name == field_name and type(field.Value) == type(value):
                    up_func = getattr(self, "update_{0}".format(field_name.lower()))
                    if up_func is None:
                        raise RuntimeError("No method to handle update")
                    return up_func(value)
            raise ValueError("Wrong field passed")
        d = self.get_device_fields()
        d.addCallback(callb)
        return d
