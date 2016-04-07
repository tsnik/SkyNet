from snp import SNPService, SNProtocolClientFactory
from Config import Config
from twisted.internet import reactor


class MainService(SNPService):
    def __init__(self):
        SNPService.__init__(self)
        self.config = Config.getconf()
        self.name = self.config.Name
        self.port = int(self.config.SkyNetServer.Port)
        self.ip = self.config.SkyNetServer.IP
        fact = SNProtocolClientFactory(self)
        reactor.connectTCP(self.ip, self.port, fact)

    def type_wel(self, request, reqid, protocol):
        protocol.sendResponse({"Type": "WEL", "Name": self.name, "Methods": []}, reqid)

    def type_cmt(self, request, reqid, protocol):
        pass
