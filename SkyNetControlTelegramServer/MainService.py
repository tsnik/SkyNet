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
        self.tg.parent = self
        self.tg.startService()

    def connectionMade(self, protocol):
        ip = protocol.transport.getPeer().host
        self.peers[ip] = protocol

    def get_devices(self):
        def callb(res):
            ret = {}
            devices = res["Devices"]
            for device in devices:
                ret[int(device["ID"])] = device["Name"]
            return ret
        d = list(self.peers.values())[0].sendRequest({"Type": "GDL"})
        d.addCallback(callb)
        return d

    def get_device_info(self, id):
        def callb(res):
            return res
        d = list(self.peers.values())[0].sendRequest({"Type": "GDF", "DevId": id})
        d.addCallback(callb)
        return d

    def get_scripts(self):
        def callb(res):
            ret = {}
            scripts = res["Scripts"]
            for script in scripts:
                ret[int(script["Id"])] = script["Name"]
            return ret
        d = list(self.peers.values())[0].sendRequest({"Type": "GSC", "Password": "Admin"})
        d.addCallback(callb)
        return d

    def update_field(self, dev_id, field, value):
        d = list(self.peers.values())[0].sendRequest({"Type": "UDF",
                                                      "DevId": dev_id, "Field": field, "Value": value})
        return d