from twisted.application import service


class SNPService(service.Service):

    def __init__(self):
        self.peers = {}

    def handleRequest(self, request, reqid, protocol):
        ip = protocol.transport.getPeer().host
        if "Type" in request:
            reqtype = request["Type"]
            if ip in self.peers or reqtype == "WEL" or reqtype == "AUR":
                thunk = getattr(self, 'type_%s' % reqtype.lower(), None)
                if thunk is None:
                    return
                try:
                    thunk(request, reqid, protocol)
                except Exception as e:
                    print(e)
                    return
            else:
                protocol.sendError(400, request)

    def connectionMade(self, protocol):
        pass

    def clientConnectionFailed(self, connector, reason):
        pass
