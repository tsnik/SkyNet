from twisted.internet import defer
from enum import Enum
from TelegramBotAPI.types.methods import sendMessage


class Activity:
    def __init__(self, manager):
        self.manager = manager
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
        self.running = True
        self.render()
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


class ActivityManager:
    def __init__(self, client, default_activity):
        self.client = client
        self.chats = {}
        self.default_activity = default_activity

    def message_received(self, message):
        chat_id = message.chat.id
        if chat_id in self.chats:
            chat = self.chats[chat_id]
            chat[len(chat) - 1].on_message(message)
        else:
            self.start_activity(chat_id, self.default_activity(self), False)

    def send_message(self, chat_id, message, keyboard):
        # TODO: Write own library or find good one instead of that
        msg = sendMessage()
        msg.chat_id = chat_id
        msg.text = message
        msg.reply_markup = '{"keyboard": ' + str(keyboard).replace("'", '"') + '}'
        self.client.send_method(msg)

    def start_activity(self, chat_id, activity, back_btn=True, **kwargs):
        def callb(res):
            self.chats[chat_id].pop()
            if not len(self.chats[chat_id]):
                self.chats.pop(chat_id)
            return res
        if chat_id not in self.chats:
            self.chats[chat_id] = []
        self.chats[chat_id].append(activity)
        d = activity.start(chat_id, self.send_message, back_btn, **kwargs)
        d.addCallback(callb)
        return d
