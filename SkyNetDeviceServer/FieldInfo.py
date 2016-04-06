import json


class FieldInfo:
    types = {int: "int",
             str: "str",
             bool: "bool"}

    def __init__(self, name, writable, value):
        self.Name = name
        self.Writable = writable
        self.Value = value

    def to_json(self):
        dic = self.__dict__()
        dic["Type"] = FieldInfo.types[type(self.value)]
        return json.dumps(dic)

    @staticmethod
    def create_from_dict(jdict):
        return FieldInfo(jdict["Name"], jdict["Writable"], jdict["Value"])
