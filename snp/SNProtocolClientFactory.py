from twisted.internet.protocol import ClientFactory
from snp import SNProtocol


class SNProtocolClientFactory(ClientFactory):
    protocol = SNProtocol

    def __init__(self, service, deferred):
        self.service = service
        self.requests = {}
        self.deferred = deferred

    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.errback(reason)



