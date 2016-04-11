from Activity import Activity


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


class DevicesActivity(Activity):
    def gen_text(self):
        self.text = "Выберите устройство"

    def gen_keyboard(self):
        pass


class ScriptsActivity(Activity):
    def gen_text(self):
        self.text = "Выберите скрипт"

    def gen_keyboard(self):
        pass


class DeviceServersActivity(Activity):
    def gen_text(self):
        self.text = "Выберите сервер устройств"

    def gen_keyboard(self):
        pass
