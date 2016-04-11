from twisted.application import service
from TelegramBot.client.twistedclient import TwistedClient
from Activity import ActivityManager
from Activities import WelcomeActivity


class TelegramService(service.Service):
    def __init__(self, token):
        self.bot = TwistedClient(token, self.on_update)
        self.manager = ActivityManager(self.bot, WelcomeActivity)

    def on_update(self, message):
        self.manager.message_received(message)

    def startService(self):
        self.bot.startService()
