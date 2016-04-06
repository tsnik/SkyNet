import json


class FieldInfo:
    types = {int: "int",
             str: "str",
             bool: "bool"}

    def __init__(self, name, writable, value):
        self.Name = name
        self.Writable = writable
        self.Value = value

    def to_dict(self):
        dic = self.__dict__
        dic["Type"] = FieldInfo.types[type(self.Value)]
        return dic

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def create_from_dict(jdict):
        return FieldInfo(jdict["Name"], jdict["Writable"], jdict["Value"])
