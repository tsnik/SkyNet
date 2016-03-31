from twisted.internet.protocol import ServerFactory
from snp import SNProtocol


class SNProtocolServerFactory(ServerFactory):
    protocol = SNProtocol

    def __init__(self, service):
        self.service = service
        self.requests = {}