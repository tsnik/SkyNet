from enum import Enum
from twisted.internet import defer
import json


class Trigger:
    jtype = "DEF"

    def check_trigger(self, field):
        d = defer.Deferred()
        d.callback(False)
        return d

    def to_dict(self):
        return {"Type": self.jtype}

    @staticmethod
    def create_from_dict(jdic):
        try:
            return trigger_types[jdic["Type"]].create_from_dict(jdic)
        except KeyError:
            raise ValueError("No such trigger type exists")


class ValueTrigger(Trigger):
    jtype = "VCH"

    @staticmethod
    def check_notequal(res, field):
        field_value = res
        return field["Value"] != field_value

    @staticmethod
    def check_equal(res, field):
        field_value = res
        return field["Value"] == field_value

    @staticmethod
    def check_greater(res, field):
        field_value = res
        return field["Value"] > field_value

    @staticmethod
    def check_less(res, field):
        field_value = res
        return field["Value"] < field_value

    @staticmethod
    def create_from_dict(jdict):
        if jdict["ChangeType"] not in value_trigger_types:
            raise ValueError("No such change type exists")
        return ValueTrigger(jdict["DevId"], jdict["FieldName"], jdict["ChangeType"],
                            FieldValue.create_from_dict(jdict["Value"]))

    def to_dict(self):
        jdic = Trigger.to_dict(self)
        jdic["DevId"] = self.devid
        jdic["FieldName"] = self.field_name
        jdic["ChangeType"] = self.type
        jdic["Value"] = self.value.to_dict()
        return jdic

    def __init__(self, devid, field_name, type, value):
        self.devid = devid
        self.field_name = field_name
        self.type = type
        self.value = value

    def get_field(self, field):
        if self.devid == field["DevId"] and self.field_name == field["Name"]:
            d = defer.Deferred()
            d.callback(field)
        else:
            d = DB.get_field_value(self.devid, self.field_name)
            d.addCallback(lambda res: {"Value": res})
        return d

    @defer.inlineCallbacks
    def check_trigger(self, field):
        try:
            field = yield self.get_field(field)
            value = yield self.value.get_value(field)
            method = getattr(ValueTrigger, "check_{0}".format(self.type))
            yield method(value, field)
        except:  # TODO: Narrow exception
            yield False


class LogicalTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    @staticmethod
    def logic_check(res):
        return False

    def check_trigger(self, field):
        d = defer.gatherResults([self.trigger1.check_trigger(field), self.trigger2.check_trigger(field)])
        d.addCallback(self.logic_check)

    def to_dict(self):
        jdic = Trigger.to_dict(self)
        jdic["Trigger1"] = self.trigger1.to_dict()
        jdic["Trigger2"] = self.trigger2.to_dict()
        return jdic


class ANDTrigger(LogicalTrigger):
    jtype = "AND"

    @staticmethod
    def logic_check(res):
        return res[0] and res[1]

    @staticmethod
    def create_from_dict(jdict):
        return ANDTrigger(Trigger.create_from_dict(jdict["Trigger1"]),
                          Trigger.create_from_dict(jdict["Trigger2"]))


class ORTrigger(LogicalTrigger):
    jtype = "OR"

    @staticmethod
    def logic_check(res):
        return res[0] or res[1]

    @staticmethod
    def create_from_dict(jdict):
        return ORTrigger(Trigger.create_from_dict(jdict["Trigger1"]),
                         Trigger.create_from_dict(jdict["Trigger2"]))


class Action:
    jtype = "DEF"

    @staticmethod
    def create_from_dict(jdic):
        try:
            return action_types[jdic["Type"]].create_from_dict(jdic)
        except KeyError:
            raise ValueError("No such action type exists")

    def execute(self):
        pass

    def to_dict(self):
        return {"Type": self.jtype}


class ChangeFieldAction(Action):
    jtype = "CHF"

    def __init__(self, devid, field, value):
        self.devid = devid
        self.field = field
        self.value = value

    def execute(self):
        def callb(res):
            # TODO: Call to remote server
            pass

        d = self.value.get_value()
        d.addCallback(callb)
        return d

    def to_dict(self):
        jdict = Action.to_dict(self)
        jdict["DevId"] = self.devid
        jdict["FieldName"] = self.field
        jdict["Value"] = self.value.to_dict()
        return jdict

    @staticmethod
    def create_from_dict(jdic):
        return ChangeFieldAction(jdic["DevId"], jdic["FieldName"],
                                 FieldValue.create_from_dict(jdic["Value"]))


class MethodAction(Action):
    def execute(self):
        pass


class MultiAction(Action):
    jtype = "MUA"

    def __init__(self, actions):
        self.actions = actions

    @defer.inlineCallbacks
    def execute(self):
        for action in self.actions:
            yield action.execute()

    def to_dict(self):
        rdict = Action.to_dict(self)
        rdict["Actions"] = [action.to_dict() for action in self.actions]
        return rdict

    @staticmethod
    def create_from_dict(jdic):
        actions = list(map(Action.create_from_dic), jdic["Actions"])
        return MultiAction(actions)


class FieldValue:
    jtype = "DEF"

    def get_value(self, ):
        """
        Gets value of FieldValue
        :rtype: Deferred
        """
        pass

    def to_dict(self):
        return {"Type": self.jtype}

    @staticmethod
    def create_from_dict(jdic):
        try:
            return field_value_types[jdic["Type"]].create_from_dict(jdic)
        except KeyError:
            raise ValueError("No such field value type exists")


class StaticFieldValue(FieldValue):
    jtype = "VAL"
    valueTypes = {int: 'int', str: 'str', bool: 'bool'}

    def __init__(self, value):
        if type(value) not in StaticFieldValue.valueTypes:
            raise ValueError("Wrong value type")
        self.value = value

    def get_value(self):
        d = defer.Deferred()
        d.callback(self.value)
        return d

    def to_dict(self):
        jdic = FieldValue.to_dict(self)
        jdic["Value"] = self.value
        return jdic

    @staticmethod
    def create_from_dict(jdic):
        return StaticFieldValue(jdic["Value"])


class DynamicFieldValue(FieldValue):
    def __init__(self, devid, field_name):
        self.devid = devid
        self.field_name = field_name

    def to_dict(self):
        jdic = FieldValue.to_dict(self)
        jdic["DevId"] = self.devid
        jdic["FieldName"] = self.field_name
        return jdic


class LocalFieldValue(DynamicFieldValue):
    jtype = "LFV"

    def get_value(self):
        d = DB.get_field_value(self.devid, self.field_name)
        return d

    @staticmethod
    def create_from_dict(jdic):
        return LocalFieldValue(jdic["DevId"], jdic["FieldName"])


class RemoteFieldValue(DynamicFieldValue):
    jtype = "RFV"

    def get_value(self):
        d = defer.Deferred()  # TODO: Request to remote server to get value
        return d

    @staticmethod
    def create_from_dict(jdic):
        return RemoteFieldValue(jdic["DevId"], jdic["FieldName"])


class Script:
    def __init__(self, trigger, action, name, id = 0):
        self.trigger = trigger
        self.action = action
        self.name = name
        self.id = id

    def doif(self, field):
        def callb(res):
            if res:
                return self.action.execute()
            return

        d = self.trigger.check_trigger(field)
        d.addCallback(callb)
        return d

    def to_dict(self):
        return {"Id": self.id,
                "Name": self.name,
                "Trigger": self.trigger.to_dict(),
                "Action": self.action.to_dict()}

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def create_from_dict(jdic):
        sid = 0
        if "Id" in jdic:
            sid = jdic["Id"]
        return Script(Trigger.create_from_dict(jdic["Trigger"]),
                      Action.create_from_dict(jdic["Action"]), jdic["Name"], sid)


action_types = {"CHF": ChangeFieldAction,
                "MTH": MethodAction,
                "MUA": MultiAction}
field_value_types = {"VAL": StaticFieldValue,
                     "LFV": LocalFieldValue,
                     "RFV": RemoteFieldValue}
trigger_types = {"VCH": ValueTrigger,
                 "AND": ANDTrigger,
                 "OR": ORTrigger}
value_trigger_types = {"NOTEQUAL", "EQUAL", "LESS", "GREATER"}
