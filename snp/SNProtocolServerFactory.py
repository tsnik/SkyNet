from twisted.internet.protocol import ServerFactory
from snp.SNProtocol import SNProtocol


class SNProtocolServerFactory(ServerFactory):
    protocol = SNProtocol

    def __init__(self, service):
        self.service = service
        self.requests = {}