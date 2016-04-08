from snp import SNPService, SNProtocolClientFactory
from Config import Config
from twisted.internet import reactor
from TelegramService import TelegramService


class MainService(SNPService):
    def __init__(self):
        SNPService.__init__(self)
        self.config = Config.getconf()
        self.name = self.config.Name
        self.port = int(self.config.SkyNetServer.Port)
        self.ip = self.config.SkyNetServer.IP
        self.tg = TelegramService(self.config.Token)

    def type_wel(self, request, reqid, protocol):
        protocol.sendResponse({"Type": "WEL", "Name": self.name, "Methods": []}, reqid)

    def type_cmt(self, request, reqid, protocol):
        pass

    def startService(self):
        fact = SNProtocolClientFactory(self)
        reactor.connectTCP(self.ip, self.port, fact)
        self.tg.startService()
