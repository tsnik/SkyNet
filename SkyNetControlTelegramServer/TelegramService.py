from twisted.application import service
from TelegramBot.client.twistedclient import TwistedClient


class TelegramService(service.Service):
    def __init__(self, token):
        self.bot = TwistedClient(token, self.on_update)

    def on_update(self, message):
        print(message)

    def startService(self):
        self.bot.startService()
