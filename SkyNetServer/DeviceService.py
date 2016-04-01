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

    def connectionMade(self, protocol):
        pass

    def type_fch(self, request, reqid, protocol):
        ip = protocol.transport.getPeer().host

        def callb(res):
            self.parent.field_updated(res, request["Field"])
        DB.get_local_devid_from_remote(ip, request["DevId"]).addCallback(callb)