from drivers.SimpleDriver import SimpleDriver
from FieldInfo import FieldInfo
from twisted.internet import defer


class TestDriver(SimpleDriver):
    def __init__(self, did, name, updated):
        SimpleDriver.__init__(self, did, name, updated)
        self.fields = [FieldInfo("Integer", True, 1), FieldInfo("String", True, 'Text'),
                       FieldInfo("Logic", True, False)]
        print("Loaded")
        print(self.fields)

    def get_device_fields(self):
        fields = {}
        for field in self.fields:
            fields[field.Name] = field
        d = defer.Deferred()
        d.callback(fields)
        return d

    def update_integer(self, value):
        self.fields[0].Value = value
        self.updated(self, "Integer", value)
        return self.fields[0]

    def update_string(self, value):
        self.fields[1].Value = value
        self.updated(self, "String", value)
        return self.fields[1]

    def update_logic(self, value):
        self.fields[2].Value = value
        self.updated(self, "Logic", value)
        return self.fields[2]