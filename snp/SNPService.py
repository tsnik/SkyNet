from twisted.application import service


class SNPService(service.Service):

    def handleRequest(self, request):
        if "Type" in request:
            reqtype = request["Type"]
            thunk = getattr(self, 'type_%s' % reqtype, None)
            if thunk is None:
                return
            try:
                thunk(request)
            except:
                return
