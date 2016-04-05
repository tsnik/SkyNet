from enum import Enum
from twisted.internet import defer
from DB import DB


class Trigger:
    def check_trigger(self, field):
        d = defer.Deferred()
        d.callback(False)
        return d

    @staticmethod
    def create_from_dict(jdic):
        try:
            return trigger_types[jdic["Type"]].create_from_dict(jdic)
        except KeyError:
            raise ValueError("No such trigger type exists")


class ValueTrigger(Trigger):
    class Type(Enum):
        NOTEQUAL = 0
        EQUAL = 1
        GREATER = 2
        LESS = 3

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
        change_type = getattr(ValueTrigger.Type, jdict["ChangeType"], None)
        if change_type is None:
            raise ValueError("No such change type exists")
        return ValueTrigger(jdict["DevId"], jdict["FieldName"], change_type,
                            FieldValue.create_from_dict(jdict["Value"]))

    type_methods = {Type.NOTEQUAL: check_notequal,
                    Type.EQUAL: check_equal,
                    Type.GREATER: check_greater,
                    Type.LESS: check_less}

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
            yield ValueTrigger.type_methods[self.type](value, field)
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


class ANDTrigger(LogicalTrigger):
    @staticmethod
    def logic_check(res):
        return res[0] and res[1]

    @staticmethod
    def create_from_dict(jdict):
        return ANDTrigger(Trigger.create_from_dict(jdict["Trigger1"]),
                          Trigger.create_from_dict(jdict["Trigger2"]))


class ORTrigger(LogicalTrigger):
    @staticmethod
    def logic_check(res):
        return res[0] or res[1]

    @staticmethod
    def create_from_dict(jdict):
        return ORTrigger(Trigger.create_from_dict(jdict["Trigger1"]),
                         Trigger.create_from_dict(jdict["Trigger2"]))


class Action:
    @staticmethod
    def create_from_dict(jdic):
        try:
            return action_types[jdic["Type"]].create_from_dict(jdic)
        except KeyError:
            raise ValueError("No such action type exists")

    def execute(self):
        pass


class ChangeFieldAction(Action):
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

    @staticmethod
    def create_from_dict(jdic):
        return ChangeFieldAction(jdic["DevId"], jdic["FieldName"],
                                 FieldValue.create_from_dict(jdic["Value"]))


class MethodAction(Action):
    def execute(self):
        pass


class MultiAction(Action):
    def __init__(self, actions):
        self.actions = actions

    @defer.inlineCallbacks
    def execute(self):
        for action in self.actions:
            yield action.execute()

    @staticmethod
    def create_from_dict(jdic):
        actions = list(map(Action.create_from_dic), jdic["Actions"])
        return MultiAction(actions)


class FieldValue:
    def get_value(self, ):
        """
        Gets value of FieldValue
        :rtype: Deferred
        """
        pass

    @staticmethod
    def create_from_dict(jdic):
        try:
            return field_value_types[jdic["Type"]].create_from_dict(jdic)
        except KeyError:
            raise ValueError("No such field value type exists")


class StaticFieldValue(FieldValue):
    valueTypes = {int: 'int', str: 'str', bool: 'bool'}

    def __init__(self, value):
        if type(value) not in StaticFieldValue.valueTypes:
            raise ValueError("Wrong value type")
        self.value = value

    def get_value(self):
        d = defer.Deferred()
        d.callback(self.value)
        return d

    @staticmethod
    def create_from_dict(jdic):
        return StaticFieldValue(jdic["Value"])


class DynamicFieldValue(FieldValue):
    def __init__(self, devid, field_name):
        self.devid = devid
        self.field_name = field_name


class LocalFieldValue(DynamicFieldValue):
    def get_value(self):
        d = DB.get_field_value(self.devid, self.field_name)
        return d

    @staticmethod
    def create_from_dict(jdic):
        return LocalFieldValue(jdic["DevId"], jdic["FieldName"])


class RemoteFieldValue(DynamicFieldValue):
    def get_value(self):
        d = defer.Deferred()  # TODO: Request to remote server to get value
        return d

    @staticmethod
    def create_from_dict(jdic):
        return RemoteFieldValue(jdic["DevId"], jdic["FieldName"])


class Script:
    def __init__(self, trigger, action):
        self.trigger = trigger
        self.action = action

    def doif(self, field):
        def callb(res):
            if res:
                return self.action.execute()
            return

        d = self.trigger.check_trigger(field)
        d.addCallback(callb)
        return d

    @staticmethod
    def create_from_dict(jdic):
        return Script(Trigger.create_from_dict(jdic["Trigger"]),
                      Action.create_from_dict(jdic["Action"]))


action_types = {"CHF": ChangeFieldAction,
                "MTH": MethodAction,
                "MUA": MultiAction}
field_value_types = {"VAL": StaticFieldValue,
                     "LFV": LocalFieldValue,
                     "RFV": RemoteFieldValue}
trigger_types = {"VCH": ValueTrigger,
                 "AND": ANDTrigger,
                 "OR": ORTrigger}
