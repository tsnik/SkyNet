from Activity import Activity, ListActivity
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
