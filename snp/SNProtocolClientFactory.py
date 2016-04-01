from twisted.internet.protocol import ClientFactory
from snp import SNProtocol


class SNProtocolClientFactory(ClientFactory):
    protocol = SNProtocol

    def __init__(self, service):
        self.service = service
        self.requests = {}

    def clientConnectionFailed(self, connector, reason):
        self.service.clientConnectionFailed(connector, reason)



