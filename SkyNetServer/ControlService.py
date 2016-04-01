from snp import SNPService, SNProtocolServerFactory
from twisted.application import internet
from DB import DB


class ControlService(SNPService):

    def __init__(self, config):
        self.factory = SNProtocolServerFactory(self)
        self.config = config
        self.port = int(config.port)
        self.iface = config.iface
        self.db = DB.get_db()
        self.controllers = {}
        self.ControlServer = internet.TCPServer(self.port, self.factory, interface=self.iface)

    def connectionMade(self, protocol):
        #TODO: Request to BD
        pass

    def startService(self):
        self.ControlServer.startService()

    def stopService(self):
        self.ControlServer.stopService()
