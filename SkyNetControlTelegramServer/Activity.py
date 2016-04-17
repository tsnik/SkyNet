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
            for i in range(len(self.keyboard), row + 1):
                self.keyboard.append([])
        if len(self.keyboard[row]) <= col:
            for i in range(len(self.keyboard[row]), col + 1):
                self.keyboard[row].append("")
        self.keyboard[row][col] = name

    def gen_text(self):
        pass

    def gen_keyboard(self):
        pass

    @defer.inlineCallbacks
    def render(self):
        self.text = ""
        self.keyboard = []
        self.actions = {}
        yield self.gen_text()
        yield self.gen_keyboard()
        if self.back_btn:
            self.keyboard.append(["Назад"])
        self.send_message(self.text, self.keyboard)
        self.running = True

    def start(self, chat_id, send_message, back_btn=True, **kwargs):
        assert callable(send_message)
        assert isinstance(chat_id, int)
        self.chat_id = chat_id
        self._send_message = send_message
        self.kwargs = kwargs
        self.render()
        self.back_btn = back_btn
        return self.deferred

    def on_message(self, text):
        if text == "Назад":
            self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.BACK))
            self.running = False
            return
        if text not in self.actions:
            self.send_message("Неверная команда", [])
            self.render()
        self.actions[text](text)

    def send_message(self, message, keyboard):
        self._send_message(self.chat_id, message, keyboard)


class ListActivity(Activity):
    DEF_ITEMS_PER_PAGE = 6
    DEF_COL_NUM = 2

    def __init__(self, manager):
        Activity.__init__(self, manager)
        self.items = {}
        self.page = 0
        self.page_num = 0
        self.items_per_page = 0
        self.col_num = 0

    @defer.inlineCallbacks
    def render(self):
        self.items = {}
        self.items_per_page = self.kwargs.get("items_per_page", ListActivity.DEF_ITEMS_PER_PAGE)
        self.col_num = self.kwargs.get("col_num", ListActivity.DEF_COL_NUM)
        yield self.gen_list()
        import math
        self.page_num = int(math.ceil(float(len(self.items)) / self.items_per_page))
        yield Activity.render(self)

    @defer.inlineCallbacks
    def gen_list(self):
        yield None

    def item_selected(self, id, item):
        pass

    def _item_selected(self, item):
        rawsplit = item.split(":")
        id = rawsplit[0]
        name = ''.join(rawsplit[1:])
        self.item_selected(id, name)

    def change_page(self, message):
        if message == "<" and self.page > 0:
            self.page -= 1
        elif message == ">" and self.page < self.page_num - 1:
            self.page += 1
        self.render()

    def gen_keyboard(self):
        start = self.page*self.items_per_page
        stop = start + self.items_per_page
        c = 0
        r = 0
        for key, item in list(self.items.items())[start:stop]:
            self.add_button("{0}:{1}".format(str(key), item), self._item_selected, r, c)
            c += 1
            if c >= self.col_num:
                c = 0
                r += 1
        if self.page > 0:
            self.add_button("<", self.change_page, r+1, 0)
        if self.page < self.page_num - 1:
            self.add_button(">", self.change_page, r+1, 1)


class WizardActivity(Activity):
    def __init__(self, manager):
        Activity.__init__(self, manager)
        self.steps = []
        self.step_results = []
        self.step_args = []

    def step_callback(self, res, step):
        if res.type == ActivityReturn.ReturnType.OK:
            self.step_results.append(res.data)
            step += 1
            if step >= len(self.steps):
                self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, self.step_results))
            else:
                self.manager.start_activity(self.chat_id, self.steps[step], self.step_args[step])\
                    .addCallback(self.step_callback, step)
        elif res.type == ActivityReturn.ReturnType.BACK:
            if step > 0:
                self.step_results.pop()
                step -= 1
                self.manager.start_activity(self.chat_id, self.steps[step]).addCallback(self.step_callback, step)
            else:
                self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.BACK))
        else:
            self.deferred.callback(res)

    def render(self):
        Activity.render(self)
        self.steps = self.kwargs.get("steps", [])
        self.step_args = self.kwargs.get("step_args", [])
        step = 0
        if step < len(self.steps):
            self.manager.start_activity(self.chat_id, self.steps[step]).addCallback(self.step_callback, step)
        else:
            self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, self.step_results))

    def gen_text(self):
        self.text = self.kwargs["text"]


class ActivityReturn:
    class ReturnType(Enum):
        OK = 0
        BACK = 1
        STOP = 2

    def __init__(self, type, data=None):
        assert isinstance(type, ActivityReturn.ReturnType)
        self.type = type
        self.data = data


class ActivityManager:
    def __init__(self, client, default_activity, serv):
        self.client = client
        self.chats = {}
        self.default_activity = default_activity
        self.serv = serv

    def message_received(self, message):
        chat_id = message.chat.id
        if chat_id in self.chats:
            chat = self.chats[chat_id]
            chat[len(chat) - 1].on_message(message.text)
        else:
            self.start_activity(chat_id, self.default_activity, False)

    def send_message(self, chat_id, message, keyboard):
        # TODO: Write own library or find good one instead of that
        msg = sendMessage()
        msg.chat_id = chat_id
        msg.text = message
        kb = False
        for row in keyboard:
            if len(row) > 0:
                kb = True
                break
        if kb:
            msg.reply_markup = '{"keyboard": ' + str(keyboard).replace("'", '"') + '}'
        self.client.send_method(msg)

    def start_activity(self, chat_id, activity, back_btn=True, **kwargs):
        def callb(res):
            self.chats[chat_id].pop()
            if not len(self.chats[chat_id]):
                self.chats.pop(chat_id)
            else:
                chat = self.chats[chat_id]
                if res.type == ActivityReturn.ReturnType.BACK:
                    chat[len(chat) - 1].render()
            return res
        if chat_id not in self.chats:
            self.chats[chat_id] = []
        act = activity(self)
        self.chats[chat_id].append(act)
        d = act.start(chat_id, self.send_message, back_btn, **kwargs)
        d.addCallback(callb)
        return d
