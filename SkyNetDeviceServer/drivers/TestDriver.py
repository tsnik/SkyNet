from drivers.SimpleDriver import SimpleDriver
from FieldInfo import FieldInfo
from twisted.internet import defer


class TestDriver(SimpleDriver):
    def __init__(self, name, updated):
        SimpleDriver.__init__(self, name, updated)
        self.fields = [FieldInfo("Integer", True, 1), FieldInfo("String", True, 'Text'),
                       FieldInfo("Logic", True, False)]
        print("Loaded")
        print(self.fields)

    def get_device_fields(self):
        fields = {}
        for field in self.fields:
            fields[field.Name] = field
        return defer.maybeDeferred(fields)

    def update_integer(self, value):
        self.fields[0].Value = value
        self.updated("Integer", self.name, value)

    def update_string(self, value):
        self.fields[1].Value = value
        self.updated("String", self.name, value)

    def update_logic(self, value):
        self.fields[2].Value = value
        self.updated("Logic", self.name, value)
