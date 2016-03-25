from twisted.internet import defer
from twisted.protocols.basic import NetstringReceiver
import json


class SNProtocol(NetstringReceiver):
    id_counter = 0

    def stringReceived(self, string):
        json_str = json.loads(string)
        self.factory.evaluatePacket(json_str)

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
