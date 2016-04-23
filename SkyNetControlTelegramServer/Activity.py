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
        if self.deferred.called:
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
        if self.deferred.called:
            self.init_defer()  # Reinit deferred
        self.deferred.callback(ActivityReturn(ActivityReturn.ReturnType.BACK))
        return self.deferred


class ListActivity(Activity):
    """
    Base class for activities with list.
    Method gen_list have to be redefined in child classes
    Method item_selected have to be redefined in child classes
    """
    DEF_ITEMS_PER_PAGE = 6
    DEF_COL_NUM = 2

    def __init__(self, manager):
        Activity.__init__(self, manager)
        self.items = {}
        self.page = 0  # Current page
        self.page_num = 0  # Total pages
        self.items_per_page = 0
        self.col_num = 0  # Number of columns on keyboard

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
        """
        Generating list.
        Fill items dictionary.
        Have to be redefined!
        """
        yield None

    def item_selected(self, id, item):
        """
        Handling item selection.
        Have to be redefined!
        :param id:
        :param item:
        """
        pass

    def _item_selected(self, item):
        """
        Get id and name and call item_selected.
        :param item: User input
        """
        rawsplit = item.split(":")
        id = rawsplit[0]
        name = ''.join(rawsplit[1:])
        self.item_selected(id, name)

    def change_page(self, message):
        """
        Handle page changes.
        :param message:
        """
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
        # Add items to keyboard
        for key, item in list(self.items.items())[start:stop]:
            self.add_button("{0}:{1}".format(str(key), item), self._item_selected, r, c)
            c += 1
            if c >= self.col_num:
                c = 0
                r += 1
        # Add navigation buttons to keyboard
        if self.page > 0:
            self.add_button("<", self.change_page, r+1, 0)
        if self.page < self.page_num - 1:
            self.add_button(">", self.change_page, r+1, 1)


class WizardActivity(LogicActivity):
    """
    Accept list of Activities and activity arguments
    Returns list of activity results
    """
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
                args = {}
                if step < len(self.step_args):
                    args = self.step_args[step]
                self.manager.start_activity(self.chat_id, self.steps[step], args)\
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
        LogicActivity.render(self)
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
    """
    Every activity should return instance of this class
    """
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
        self.client = client  # Telegram API
        self.chats = {}  # Chats
        self.default_activity = default_activity  # Activity starting for new user
        self.serv = serv  # Service, to send requests to servers

    def message_received(self, message):
        """
        Handle message from user
        :param message:
        """
        chat_id = message.chat.id
        if chat_id in self.chats:  # Call activity message handlers
            chat = self.chats[chat_id]
            chat[len(chat) - 1].on_message(message.text)
        else:  # Start default_activity on first message
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
            if step >= len(activities_list):  # if activities list finished
                if callable(wizard_completed):  # If custom finish handler
                    step -= 1
                    return self.wizard_callback(wizard_completed(res), chat_id, activities_list, step, wizard_completed)
                else:
                    chat = self.chats[chat_id]
                    for i in range(len(activities_list)):  # Remove all wizard activities from chat
                        chat.pop()
            else:  # Call next activity on list
                return self.start_activity(chat_id, activities_list[step], **res.data, add_callbacks=False)\
                    .addCallback(self.wizard_callback, chat_id, activities_list, step, wizard_completed)
        elif res.type == ActivityReturn.ReturnType.BACK:
            step -= 1
            chat = self.chats[chat_id]
            chat.pop()
            if step >= 0:  # Call previous activity on list and return it result
                return chat[len(chat) - 1].restart()\
                    .addCallback(self.wizard_callback, chat_id, activities_list, step, wizard_completed)
            else:  # Call activity before list
                chat[len(chat) - 1].restart()
        return res  # Pass others results to next callback

    def general_callback(self, res, chat_id):
        self.chats[chat_id].pop()
        if not len(self.chats[chat_id]):  # Remove chat if all activities closed
            self.chats.pop(chat_id)
        else:
            chat = self.chats[chat_id]
            if res.type == ActivityReturn.ReturnType.BACK:  # Restart previous activity on back button
                chat[len(chat) - 1].restart()
        return res

    def start_activity(self, chat_id, activity, back_btn=True, wizard_completed=None, add_callbacks=True, **kwargs):
        if chat_id not in self.chats:  # Create chat if not exists
            self.chats[chat_id] = []
        is_list = False  # List of activities passed
        if type(activity) is list:
            assert len(activity) > 0
            activities_list = activity
            activity = activity[0]
            is_list = True
        act = activity(self)
        self.chats[chat_id].append(act)
        d = act.start(chat_id, self.send_message, back_btn, **kwargs)
        if add_callbacks:
            if is_list:  # Select right callback
                d.addCallback(self.wizard_callback, chat_id, activities_list, 0, wizard_completed)
            else:
                d.addCallback(self.general_callback, chat_id)
        return d
