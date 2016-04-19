from twisted.internet import defer
from enum import Enum
from TelegramBotAPI.types.methods import sendMessage


class Activity:
    def __init__(self, manager):
        self.manager = manager  # Activity manager
        self.actions = {}  # Mapping from buttons to methods
        self.keyboard = []  # Telegram keyboard representation [[str]]
        self.text = ""  # Activity text
        self.chat_id = None  # Id of the chat where activity running
        self.deferred = None  # Deferred which is calling when activity return result
        self._send_message = None  # Method to send messages to telegram (chat_id, text, keyboard)
        self.kwargs = None  # Arguments for activity
        self.back_btn = True  # Show button back

    def add_button(self, name, action, row=-1, col=-1):
        """
        Add button to keyboard
        :param name: Button text
        :param action: Button action
        :param row: By default last row
        :param col: By default last col
        """
        assert name not in self.actions
        self.actions[name] = action
        if row == -1:
            row = len(self.keyboard)
        if len(self.keyboard) <= row:
            for i in range(len(self.keyboard), row + 1):
                self.keyboard.append([])
        if col == -1:
            col = len(self.keyboard[row])
        if len(self.keyboard[row]) <= col:
            for i in range(len(self.keyboard[row]), col + 1):
                self.keyboard[row].append("")
        self.keyboard[row][col] = name

    def gen_text(self):
        self.text = self.kwargs.get("text", "")

    def gen_keyboard(self):
        pass

    @defer.inlineCallbacks
    def render(self):
        # erase data from previous renders
        self.text = ""
        self.keyboard = []
        self.actions = {}
        # generate text and keyboard
        yield self.gen_text()
        yield self.gen_keyboard()
        if self.back_btn:
            self.keyboard.append(["Назад"])
        # send message
        self.send_message(self.text, self.keyboard)

    def start(self, chat_id, send_message, back_btn=True, **kwargs):
        """
        Start activity
        :param chat_id:  Id of the chat where activity running
        :param send_message: Method to send messages to telegram (chat_id, text, keyboard)
        :param back_btn: Show back button
        :param kwargs: Activity params
        :return: Deferred, which called with ActivityReturn
        """
        assert callable(send_message)
        assert isinstance(chat_id, int)
        self.init_defer()  # init deferred
        # set params
        self.chat_id = chat_id
        self._send_message = send_message
        self.kwargs = kwargs
        self.back_btn = back_btn
        # do rendering
        self.render()
        return self.deferred

    def restart(self):
        self.init_defer()  # Reinit deferred
        self.render()  # Rendering
        return self.deferred  # Return new deferred

    def on_message(self, text):
        if text == "Назад":  # Back button
            self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.BACK))
            return
        if text not in self.actions:  # Wrong commands
            self.send_message("Неверная команда", [])
            self.render()
            return
        self.actions[text](text)

    def send_message(self, message, keyboard):
        """
        Send message wrapper
        :param message:
        :param keyboard:
        """
        self._send_message(self.chat_id, message, keyboard)

    def init_defer(self):
        self.deferred = defer.Deferred()
        self.deferred.addCallback(self.def_callback)

    def def_callback(self, res):
        # Add input params to result for pass-thru execution
        tmp = {}
        tmp.update(self.kwargs)
        tmp.update(res.data)
        res.data = tmp
        return res


class LogicActivity(Activity):
    def render(self):
        pass

    def restart(self):
        self.deferred = defer.Deferred()
        self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.BACK))
        return self.deferred


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


class ChooseFromListActivity(ListActivity):
    def item_selected(self, id, item):
        self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.OK, (id, item)))


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
        NOTHING = 3

    def __init__(self, return_type, data={"data": None}):
        assert isinstance(return_type, ActivityReturn.ReturnType)
        self.type = return_type
        if type(data) is not dict:
            data = {"data": data}
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

    def wizard_callback(self, res, chat_id, activities_list, step, wizard_completed):
        if res.type == ActivityReturn.ReturnType.OK:
            step += 1
            if step >= len(activities_list):
                if callable(wizard_completed):
                    step -= 1
                    return self.wizard_callback(wizard_completed(res), chat_id, activities_list, step, wizard_completed)
                else:
                    chat = self.chats[chat_id]
                    for i in range(len(activities_list)):
                        chat.pop()
            else:
                return self.start_activity(chat_id, activities_list[step], **res.data, add_callbacks=False)\
                    .addCallback(self.wizard_callback, chat_id, activities_list, step, wizard_completed)
        elif res.type == ActivityReturn.ReturnType.BACK:
            step -= 1
            chat = self.chats[chat_id]
            chat.pop()
            if step >= 0:
                chat[len(chat) - 1].restart()\
                    .addCallback(self.wizard_callback, chat_id, activities_list, step, wizard_completed)
            else:
                chat[len(chat) - 1].restart()\
                    .addCallback(self.general_callback, chat_id)
        return res

    def general_callback(self, res, chat_id):
        self.chats[chat_id].pop()
        if not len(self.chats[chat_id]):
            self.chats.pop(chat_id)
        else:
            chat = self.chats[chat_id]
            if res.type == ActivityReturn.ReturnType.BACK:
                chat[len(chat) - 1].restart().addCallback(self.general_callback, chat_id)
                return res
        return res

    def start_activity(self, chat_id, activity, back_btn=True, wizard_completed=None, add_callbacks=True, **kwargs):
        if chat_id not in self.chats:
            self.chats[chat_id] = []
        is_list = False
        if type(activity) is list:
            assert len(activity) > 0
            activities_list = activity
            activity = activity[0]
            is_list = True
        act = activity(self)
        self.chats[chat_id].append(act)
        d = act.start(chat_id, self.send_message, back_btn, **kwargs)
        if add_callbacks:
            if is_list:
                d.addCallback(self.wizard_callback, chat_id, activities_list, 0, wizard_completed)
            else:
                d.addCallback(self.general_callback, chat_id)
        return d
