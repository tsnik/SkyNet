from enum import Enum
from twisted.internet import defer
from DB import DB


class Trigger:
    def check_trigger(self, field):
        return False


class ValueTrigger(Trigger):
    class Type(Enum):
        NOTEQUAL = 0
        EQUAL = 1
        GREATER = 2
        LESS = 3

    @staticmethod
    def check_notequal(res):
        field = res[0]
        field_value = res[1]
        return field["Value"] != field_value

    @staticmethod
    def check_equal(res):
        field = res[0]
        field_value = res[1]
        return field["Value"] == field_value

    @staticmethod
    def check_greater(res):
        field = res[0]
        field_value = res[1]
        return field["Value"] > field_value

    @staticmethod
    def check_less(res):
        field = res[0]
        field_value = res[1]
        return field["Value"] < field_value

    type_methods = {Type.NOTEQUAL: check_notequal,
                     Type.EQUAL: check_equal,
                     Type.GREATER: check_greater,
                     Type.LESS: check_less}

    def __init__(self, devid, field_name, type, value):
        self.devid = devid
        self.field_name = field_name
        self.type = type
        self.value = value

    def check_trigger(self, field):
        d = self.value.get_value(field)
        d.addCallback(ValueTrigger.type_methods[self.type])
        return d


class LogicalTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2


class ANDTrigger(LogicalTrigger):
    def check_trigger(self, field):
        return self.trigger1.check_trigger(field) and self.trigger2.check_trigger(field)


class ORTrigger(LogicalTrigger):
    def check_trigger(self, field):
        return self.trigger1.check_trigger(field) or self.trigger2.check_trigger(field)


class Action:
    def execute(self):
        pass


class ChangeFieldAction(Action):
    def __init__(self, devid, field):
        self.devid = 0
        self.field = ""
        self.value = 0

    def execute(self):
        def callb(res):
            # TODO: Call to remote server
            pass
        d = self.value.get_value()
        d.addCallback(callb)
        return d


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


class FieldValue:
    def get_value(self, field=""):
        """
        Gets value of FieldValue
        :param field:
        :rtype: Deferred
        """
        pass


class StaticFieldValue(FieldValue):
    def __init__(self, value):
        self.value = value

    def get_value(self, field=""):
        d = defer.Deferred()
        d.callback((field, self.value))
        return d


class DynamicFieldValue(FieldValue):
    def __init__(self, devid, field_name):
        self.devid = devid
        self.field_name = field_name


class LocalFieldValue(DynamicFieldValue):
    def get_value(self, field=""):
        def callb(res):
            return field, res
        d = DB.get_field_value(self.devid, self.field_name)
        d.addCallback(callb)
        return d


class RemoteFieldValue(DynamicFieldValue):
    def get_value(self, field=""):
        def callb(res):
            return field, res
        d = defer.Deferred()  # TODO: Request to remote server to get value
        d.addCallback(callb)
        return d


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