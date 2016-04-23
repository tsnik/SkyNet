from Activity import Activity, LogicActivity, ListActivity, ActivityReturn, WizardActivity
from twisted.internet import defer
from snp import Script
from snp.Script import ValueTrigger, ANDTrigger, ORTrigger, StaticFieldValue, LocalFieldValue, RemoteFieldValue, \
    ChangeFieldAction, MethodAction


class WelcomeActivity(Activity):
    def gen_text(self):
        self.text = "Выберите действие"

    def gen_keyboard(self):
        self.back_btn = False
        self.add_button("Устройства", self.go_to_devices, 0, 0)
        self.add_button("Скрипты", self.go_to_scripts, 1, 0)
        self.add_button("Сервера устройств", self.go_to_device_servers, 2, 0)

    def go_to_devices(self, m):
        self.manager.start_activity(self.chat_id, [DevicesActivity, DeviceInfoActivity, FieldEdit],
                                    wizard_completed=lambda res: ActivityReturn(ActivityReturn.ReturnType.BACK),
                                    writable=True)

    def go_to_scripts(self, m):
        self.manager.start_activity(self.chat_id, ScriptsActivity)

    def go_to_device_servers(self, m):
        self.manager.start_activity(self.chat_id, DeviceServersActivity)


class DevicesActivity(ListActivity):
    def gen_text(self):
        self.text = "Выберите устройство"

    @defer.inlineCallbacks
    def gen_list(self):
        self.items = yield self.manager.serv.get_devices()
        yield None

    def item_selected(self, dev_id, name):
        self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, {"dev_id": int(dev_id)}))


class DeviceInfoActivity(ListActivity):
    def __init__(self, manager):
        ListActivity.__init__(self, manager)
        self.fields = []
        self.dev_name = ""

    def gen_text(self):
        self.text = self.dev_name + "\n"
        self.text += "Поля данного устройства: \n"
        for field in self.fields:
            self.text += field["Name"] + ": " + str(field["Value"]) + "\n"

    @defer.inlineCallbacks
    def gen_list(self):
        device = yield self.manager.serv.get_device_info(self.kwargs["dev_id"])
        self.fields = device["Fields"]
        self.dev_name = device["Name"]
        field_type = self.kwargs.get("field_type", None)
        writable = self.kwargs.get("writable", None)
        self.items = {field["Name"]: field["Type"] for field in self.fields
                      if self.filter_f(field, field_type, writable)}
        yield None

    def item_selected(self, name, field_type):
        self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, {"dev_name": self.dev_name,
                                                                             "field_name": name,
                                                                             "field_type": field_type}))

    @staticmethod
    def filter_f(field, field_type, writable):
        if field_type is not None:
            if field["Type"] != field_type:
                return False
        if writable is not None:
            if field["Writable"] != writable:
                return False
        return True


class InputValue(Activity):
    types = {"int": "число", "str": "строка"}

    def gen_text(self):
        if "dev_name" in self.kwargs:
            self.text += "Редактируем устройтво {0}:\n".format(self.kwargs["dev_name"])
        if self.kwargs["field_type"] == "bool":
            self.text += "Выберите значение поля {0}:".format(self.kwargs.get("field_name", " "))
            return
        self.text += "Введите значение поля {0} типа {1}:".format(self.kwargs.get("field_name", ""),
                                                                  self.types[self.kwargs["field_type"]])

    def gen_keyboard(self):
        if self.kwargs["field_type"] == "bool":
            self.keyboard = [["Да", "Нет"]]

    def on_message(self, text):
        field_type = self.kwargs["field_type"]
        if text != "Назад":
            value = None
            if field_type == "str":
                value = text
            elif field_type == "int" and FieldEdit.is_int(text):
                value = int(text)
            elif field_type == "bool" and FieldEdit.is_bool(text):
                value = {"Да": True, "Нет": False}[text]
            if value is not None:
                self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, {"value": value}))
                return
        Activity.on_message(self, text)

    @staticmethod
    def is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_bool(s):
        return s in ["Да", "Нет"]


class FieldEdit(LogicActivity):
    @defer.inlineCallbacks
    def render(self):
        res = yield self.manager.start_activity(self.chat_id, InputValue, **self.kwargs)
        if res.type == ActivityReturn.ReturnType.OK:
            res = res.data
            self.update_field(res["dev_id"], res["field_name"], res["value"])

    def update_field(self, dev_id, name, value):
        d = self.manager.serv.update_field(dev_id, name, value)
        d.addCallbacks(self.field_updated, self.field_update_error)

    def field_updated(self, res):
        self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK))

    def field_update_error(self, err):
        pass

    @staticmethod
    def is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_bool(s):
        return s in ["Да", "Нет"]


class ScriptsActivity(ListActivity):
    def __init__(self, manager):
        super().__init__(manager)
        self.scripts = {}

    def gen_text(self):
        self.text = "Выберите скрипт"

    @defer.inlineCallbacks
    def gen_list(self):
        self.scripts = yield self.manager.serv.get_scripts()
        self.items = {script.id: script.name for script in self.scripts.values()}
        yield None

    def item_selected(self, id, name):
        self.send_message(str(id), [])
        self.send_message(name, [])

    def gen_keyboard(self):
        super().gen_keyboard()
        self.add_button("Добавить скрипт", self.add_script)

    @defer.inlineCallbacks
    def add_script(self, text):
        res = yield self.manager.start_activity(self.chat_id, [EnterNameActivity, TriggerCreateActivity,
                                                               ActionCreateActivity, ScriptCreateActivity],
                                                text="Введите имя сценария: ", key="script_name")
        if res.type == ActivityReturn.ReturnType.OK:
            script = res.data["script"]
            yield self.manager.serv.create_script(script)
            self.render()


class ScriptCreateActivity(Activity):
    @defer.inlineCallbacks
    def gen_text(self):
        self.text = "Создание скрипта..."
        name = self.kwargs["script_name"]
        trigger = self.kwargs["trigger"]
        action = self.kwargs["action"]
        self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, {"script": Script(trigger, action, name)}))
        yield None


class ActionCreateActivity(LogicActivity):
    @defer.inlineCallbacks
    def render(self):
        res = yield self.manager.start_activity(self.chat_id, [SelectItem, ActionRouterActivity],
                                                text="Выберите тип действия: ",
                                                list=["Изменение поля", "Вызов метода"])
        if res.type == ActivityReturn.ReturnType.OK:
            self.deferred.callback(res)
        yield None


class ActionRouterActivity(LogicActivity):
    types = {"Изменение поля": ChangeFieldAction, "Вызоы метода": MethodAction}

    @defer.inlineCallbacks
    def render(self):
        action_type = self.types[self.kwargs["selected_item"]]
        action = None
        if action_type == ChangeFieldAction:
            res = yield self.manager.start_activity(self.chat_id, [DevicesActivity, DeviceInfoActivity,
                                                                   FieldValueCreateActivity],
                                                    text="Выберите тип изменения", list=["GREATER", "LESS",
                                                                                         "EQUAL", "NOTEQUAL"],
                                                    writable=True)
            if res.type == ActivityReturn.ReturnType.OK:
                dev_id = res.data["dev_id"]
                field_name = res.data["field_name"]
                field_value = res.data["field_value"]
                action = ChangeFieldAction(dev_id, field_name, field_value)
        elif action_type == MethodAction:
            pass
        if action is not None:
            self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, {"action": action}))
        pass


class TriggerCreateActivity(LogicActivity):
    @defer.inlineCallbacks
    def render(self):
        res = yield self.manager.start_activity(self.chat_id, [SelectItem, TriggerRouterActivity],
                                                text="Выберите тип триггера: ",
                                                list=["Изменение поля", "И триггер", "ИЛИ триггер"])
        if res.type == ActivityReturn.ReturnType.OK:
            self.deferred.callback(res)
        yield None


class TriggerRouterActivity(LogicActivity):
    types = {"Изменение поля": ValueTrigger, "И триггер": ANDTrigger, "ИЛИ триггер": ORTrigger}

    @defer.inlineCallbacks
    def render(self):
        trigger_type = TriggerRouterActivity.types[self.kwargs["selected_item"]]
        trigger = None
        if trigger_type == ValueTrigger:
            res = yield self.manager.start_activity(self.chat_id, [DevicesActivity, DeviceInfoActivity,
                                                                   SelectItem, FieldValueCreateActivity],
                                                    text="Выберите тип изменения", list=["GREATER", "LESS",
                                                                                         "EQUAL", "NOTEQUAL"])
            if res.type == ActivityReturn.ReturnType.OK:
                dev_id = res.data["dev_id"]
                field_name = res.data["field_name"]
                change_type = res.data["selected_item"]
                field_value = res.data["field_value"]
                trigger = ValueTrigger(dev_id, field_name, change_type, field_value)
        elif trigger_type == ANDTrigger or trigger_type == ORTrigger:
            if trigger_type == ANDTrigger:
                self.send_message("Создание И триггера.", [[]])
            elif trigger_type == ORTrigger:
                self.send_message("Создание ИЛИ триггера.", [[]])
            res = yield self.manager.start_activity(self.chat_id, WizardActivity,
                                                    steps=[TriggerCreateActivity, TriggerCreateActivity])
            if res.type == ActivityReturn.ReturnType.OK:
                trigger1 = res.data["data"][0]["trigger"]
                trigger2 = res.data["data"][1]["trigger"]
                trigger = trigger_type(trigger1, trigger2)
        if trigger is not None:
            self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, {"trigger": trigger}))


class FieldValueCreateActivity(LogicActivity):
    @defer.inlineCallbacks
    def render(self):
        res = yield self.manager.start_activity(self.chat_id, [SelectItem, FieldValueRouterActivity],
                                                field_type=self.kwargs["field_type"],
                                                text="Выберите тип значения: ",
                                                list=["Статическое значение", "Локальное поле", "Удаленное поле"])
        if res.type == ActivityReturn.ReturnType.OK:
            self.deferred.callback(res)
        yield None


class FieldValueRouterActivity(LogicActivity):
    types = {"Статическое значение": StaticFieldValue, "Локальное поле": LocalFieldValue,
             "Удаленное поле": RemoteFieldValue}

    @defer.inlineCallbacks
    def render(self):
        type = self.types[self.kwargs["selected_item"]]
        field_value = None
        if type == StaticFieldValue:
            res = yield self.manager.start_activity(self.chat_id, InputValue, **self.kwargs)
            if res.type == ActivityReturn.ReturnType.OK:
                value = res.data["value"]
                field_value = StaticFieldValue(value)
        elif type == LocalFieldValue:
            res = yield self.manager.start_activity(self.chat_id, [DevicesActivity, DeviceInfoActivity], **self.kwargs)
            if res.type == ActivityReturn.ReturnType.OK:
                dev_id = res.data["dev_id"]
                field_name = res.data["field_name"]
                field_value = LocalFieldValue(dev_id, field_name)
        elif type == RemoteFieldValue:
            res = yield self.manager.start_activity(self.chat_id, [DevicesActivity, DeviceInfoActivity], **self.kwargs)
            if res.type == ActivityReturn.ReturnType.OK:
                dev_id = res.data["dev_id"]
                field_name = res.data["field_name"]
                field_value = RemoteFieldValue(dev_id, field_name)
        if field_value is not None:
            self.kwargs = {}
            self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, {"field_value": field_value}))


class EnterNameActivity(Activity):
    def gen_text(self):
        self.text = self.kwargs["text"]

    def on_message(self, text):
        dict_key = self.kwargs.get("key", "name")
        if text != "Назад":
            self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, {dict_key: text}))
            return
        Activity.on_message(self, text)


class SelectItem(ListActivity):
    def gen_list(self):
        l = self.kwargs["list"]
        self.items = {i: l[i] for i in range(len(l))}

    def item_selected(self, id, name):
        self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, {"selected_item": name}))


class DeviceServersActivity(ListActivity):
    def gen_text(self):
        self.text = "Выберите сервер устройств"

    @defer.inlineCallbacks
    def gen_list(self):
        self.items = yield self.manager.serv.get_servers()
        yield None

    #def item_selected(self, dev_id, name):
    #    self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, {"dev_id": int(dev_id)}))

    def gen_keyboard(self):
        super().gen_keyboard()
