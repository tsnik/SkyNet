from twisted.internet import defer
from twisted.protocols.basic import NetstringReceiver
import json


class SNError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, args, kwargs)
        self.code = args[1]
        self.request = args[2]


class SNProtocol(NetstringReceiver):
    id_counter = 0

    def stringReceived(self, string):
        packet = json.loads(string)
        if "reqid" in packet:
            if len(packet["reqid"]) > 2:
                type = packet["reqid"][:2]
                reqid = packet["reqid"][2:]
                if type == "RQ":
                    self.factory.service.hadleRequest(packet, reqid, self)
                elif type == "RE":
                    if reqid in self.requests:
                        self.factory.requests[reqid].callback(packet)
                        self.factory.requests.pop(reqid)

    def sendRequest(self, request):
        reqid = str(self.id_counter)
        request["reqid"] = "RQ{0}".format(reqid)
        self._sendPacket(request)
        d = self.createDeferred(reqid)
        self.id_counter += 1
        return d

    def sendResponse(self, request, reqid):
        request["reqid"] = "RE{0}".format(str(reqid))
        self._sendPacket(request)

    def sendError(self, code, request):
        reqid = request["reqid"][2:]
        r = {"Error": code, "Request": request, "reqid": "RE{0}".format(str(reqid))}
        self._sendPacket(r)

    def _sendPacket(self, request):
        json_str = json.dumps(request)
        self.sendString(json_str.encode("ascii"))

    def connectionMade(self):
        self.factory.service.connectionMade(self)

    def createDeferred(self, reqid):
        d = defer.Deferred()
        d.addCallback(self.errorChecker)
        self.factory.requests[reqid] = d
        return d

    def errorChecker(self, packet):
        if "Error" in packet:
            raise SNError("", int(packet["Error"]), packet["Request"])
        return packet
