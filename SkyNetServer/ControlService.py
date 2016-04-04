from snp import SNPService, SNProtocolServerFactory
from twisted.application import internet
from DB import DB


class ControlService(SNPService):

    def __init__(self, config):
        SNPService.__init__(self)
        self.factory = SNProtocolServerFactory(self)
        self.config = config
        self.port = int(config.port)
        self.iface = config.iface
        self.db = DB.get_db()
        self.ControlServer = internet.TCPServer(self.port, self.factory, interface=self.iface)

    def connectionMade(self, protocol):
        ip = protocol.transport.getPeer().host

        def callb(res):
            DB.update_methods(ip, res["Name"], res["Methods"])
            self.peers[ip] = protocol
        #TODO: Request to BD
        protocol.sendRequest({"Type": "WEL", "Name": self.config.name}).addCallback(callb)

    def startService(self):
        self.ControlServer.startService()

    def stopService(self):
        self.ControlServer.stopService()

    def type_gdl(self, request, reqid, protocol):
        pass
