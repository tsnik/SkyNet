from twisted.internet.protocol import ServerFactory
from snp import SNProtocol


class SNProtocolServerFactory(ServerFactory):
    protocol = SNProtocol

    def __init__(self, service):
        self.service = service
        self.requests = {}

    def evaluatePacket(self, packet):
        packet = {}
        if "reqid" in packet:
            if len(packet["reqid"]) > 2:
                type = packet["reqid"][:2]
                reqid = int(packet["reqid"][2:])
                if type == "RQ":
                    self.service.hadleRequest(packet, reqid)
                elif type == "RE":
                    if reqid in self.requests:
                        self.requests[reqid].callback(packet)