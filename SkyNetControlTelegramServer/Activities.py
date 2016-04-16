from Activity import Activity, ListActivity, ActivityReturn
from twisted.internet import defer


class WelcomeActivity(Activity):
    def gen_text(self):
        self.text = "Выберите действие"

    def gen_keyboard(self):
        self.back_btn = False
        self.add_button("Устройства", self.go_to_devices, 0, 0)
        self.add_button("Скрипты", self.go_to_scripts, 1, 0)
        self.add_button("Сервера устройств", self.go_to_device_servers, 2, 0)

    def go_to_devices(self, m):
        self.manager.start_activity(self.chat_id, DevicesActivity)
        pass

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

    def item_selected(self, DevId, name):
        self.manager.start_activity(self.chat_id, DeviceInfoActivity, id=int(DevId))


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
        res = yield self.manager.serv.get_device_info(self.kwargs["id"])
        device = res["Device"]
        self.fields = device["Fields"]
        self.dev_name = device["Name"]
        self.items = {field["Name"]: field["Type"] for field in self.fields if field["Writable"]}
        yield None

    def item_selected(self, name, field_type):
        d = self.manager.start_activity(self.chat_id, FieldEdit,
                                    dev_id=self.kwargs["id"], dev_name=self.dev_name,
                                    field_name=name, field_type=field_type)
        d.addCallback(self.field_update_callback)

    @defer.inlineCallbacks
    def field_update_callback(self, res):
        if res.type == ActivityReturn.ReturnType.OK:
            name, value = res.data
            yield self.manager.serv.update_field(self.kwargs["id"], name, value)
            self.render()
        yield None


class FieldEdit(Activity):
    types = {"int": "число", "str": "строка"}

    def gen_text(self):
        self.text = "Редактируем устройтво {0}:\n".format(self.kwargs["dev_name"])
        if self.kwargs["field_type"] == "bool":
            self.text += "Выберите значение поля {0}:".format(self.kwargs["field_name"])
            return
        self.text += "Введите значение поля {0} типа {1}:".format(self.kwargs["field_name"],
                                                                  self.types[self.kwargs["field_type"]])

    def gen_keyboard(self):
        if self.kwargs["field_type"] == "bool":
            self.keyboard = [["Да", "Нет"]]

    def on_message(self, text):
        field_type = self.kwargs["field_type"]
        field_name = self.kwargs["field_name"]
        if text != "Назад":
            if field_type == "str":
                self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, (field_name, text)))
                return
            elif field_type == "int" and FieldEdit.is_int(text):
                self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, (field_name, int(text))))
                return
            elif field_type == "bool" and FieldEdit.is_bool(text):
                self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK,
                                                      (field_name, {"Да": True, "Нет": False}[text])))
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


class ScriptsActivity(ListActivity):
    def gen_text(self):
        self.text = "Выберите скрипт"

    @defer.inlineCallbacks
    def gen_list(self):
        self.items = yield self.manager.serv.get_scripts()
        yield None

    def item_selected(self, id, name):
        self.send_message(str(id), [])
        self.send_message(name, [])


class DeviceServersActivity(Activity):
    def gen_text(self):
        self.text = "Выберите сервер устройств"

    def gen_keyboard(self):
        pass
