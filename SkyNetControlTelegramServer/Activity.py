from twisted.internet import defer
from enum import Enum


class Activity:
    def __init__(self):
        self.actions = {}
        self.keyboard = []
        self.text = ""
        self.chat_id = None
        self.deferred = defer.Deferred()
        self._send_message = None
        self.kwargs = None
        self.running = False
        self.back_btn = True

    def add_button(self, name, action, row, col):
        assert name not in self.actions
        self.actions[name] = action
        if len(self.keyboard) <= row:
            for i in range(len(self.keyboard), row):
                self.keyboard.append([])
        if len(self.keyboard[row]) <= col:
            for i in range(len(self.keyboard[row]), col):
                self.keyboard[row].append("")
        self.keyboard[row][col] = name
        if self.back_btn:
            self.keyboard.append("Назад")

    def gen_text(self):
        pass

    def gen_keyboard(self):
        pass

    def render(self):
        self.gen_text()
        self.gen_keyboard()
        assert self.running
        self.send_message(self.text, self.keyboard)

    def start(self, chat_id, send_message, back_btn=True, **kwargs):
        assert callable(send_message)
        assert isinstance(chat_id, int)
        self.chat_id = chat_id
        self._send_message = send_message
        self.kwargs = kwargs
        self.render()
        self.running = True
        self.back_btn = back_btn
        return self.deferred

    def on_message(self, message):
        if message.text == "Назад":
            self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.BACK))
            self.running = False
            return
        if message.text not in self.actions:
            self.send_message("Неверная команда", [])
            return
        self.actions[message](message)

    def send_message(self, message, keyboard):
        assert self.running
        self._send_message(self.chat_id, message, keyboard)


class ActivityReturn:
    class ReturnType(Enum):
        OK = 0
        BACK = 1
        STOP = 2

    def __init__(self, type, data=None):
        assert isinstance(type, ActivityReturn.ReturnType)
        self.type = ""
        self.data = data
