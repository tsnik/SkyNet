from enum import Enum


class Trigger:
    def check_trigger(self, field):
        return False


class ValueTrigger(Trigger):
    class Type(Enum):
        DEFAULT = 0
        EQUAL = 1
        GREATER = 2
        LESS = 3

    def __init__(self, devid, field_name, type, value):
        self.devid = devid
        self.field_name = field_name
        self.type = type
        self.value = value

    def check_trigger(self, field):
        # TODO
        pass


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
