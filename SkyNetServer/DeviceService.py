from snp import SNPService, SNProtocolClientFactory
from DB import DB


class DeviceService(SNPService):

    def __init__(self, config):
        self.config = config

    def startService(self):
        def callb(res):
            from twisted.internet import reactor
            for dev in res:
                fact = SNProtocolClientFactory(self)
                reactor.connectTCP(dev[1], dev[2], fact)
        DB.get_device_servers().addCallback(callb)
        pass

    def connectionMade(self, protocol):
        pass
