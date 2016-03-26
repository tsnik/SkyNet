from twisted.internet import defer
from twisted.protocols.basic import NetstringReceiver
import json


class SNProtocol(NetstringReceiver):
    id_counter = 0

    def stringReceived(self, string):
        packet = json.loads(string)
        if "reqid" in packet:
            if len(packet["reqid"]) > 2:
                type = packet["reqid"][:2]
                reqid = int(packet["reqid"][2:])
                if type == "RQ":
                    self.factory.service.hadleRequest(packet, reqid)
                elif type == "RE":
                    if reqid in self.requests:
                        self.factory.requests[reqid].callback(packet)

    def sendRequest(self, request):
        request["reqid"] = "RQ{0}".format(str(SNProtocol.id_counter))
        self._sendPacket(request)
        d = defer.Deferred()
        d.addCallback(self.errorChecker)
        self.factory.service.requests[SNProtocol.id_counter] = d
        SNProtocol.id_counter += 1
        return d

    def sendResponse(self, request, reqid):
        request["reqid"] = "RE{0}".format(str(reqid))
        self._sendPacket(request)

    def _sendPacket(self, request):
        json_str = json.dumps(request)
        self.sendString(json_str)

    def errorChecker(self, packet):
        # TODO: Implement error checker
        return packet
