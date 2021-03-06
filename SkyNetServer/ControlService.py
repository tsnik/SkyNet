from snp import SNPService, SNProtocolServerFactory, CertManager
from twisted.internet import ssl
from DB import DB
from snp.Script import Script


class ControlService(SNPService):

    def __init__(self, config):
        SNPService.__init__(self)
        self.factory = SNProtocolServerFactory(self)
        self.config = config
        self.port = int(config.port)
        self.iface = config.iface
        self.db = DB.get_db()
        self.cert_manager = CertManager("keys", "control_servers", self.config.name)

        sslcontext = ssl.DefaultOpenSSLContextFactory('keys/' + self.config.name + '.key',
                                                      'keys/' + self.config.name + '.crt')
        self.ControlServer = self.cert_manager.create_server(self.port, self.factory, self.iface)

    def connectionMade(self, protocol):
        ip = protocol.transport.getPeer().host

        def callb(res):
            DB.update_methods(ip, res["Name"], res["Methods"])
            self.peers[ip] = protocol
        #  TODO: Request to BD
        protocol.sendRequest({"Type": "WEL", "Name": self.config.name}).addCallback(callb)

    def startService(self):
        self.ControlServer.startService()

    def stopService(self):
        self.ControlServer.stopService()

    def type_gdl(self, request, reqid, protocol):
        def callb(res):
            response = {"Devices": res}
            protocol.sendResponse(response, reqid)
        DB.get_devices().addCallback(callb)

    def type_gdf(self, request, reqid, protocol):
        def callb(res):
            protocol.sendResponse({"Type": "GDF", "Device": res}, reqid)
        d = self.parent.get_device_data(request["DevId"])
        d.addCallback(callb)

    def type_udf(self, request, reqid, protocol):
        def callb(res):
            protocol.sendResponse(res, reqid)
        self.parent.update_device_field(request["DevId"], request["Field"], request["Value"]).addCallback(callb)

    def check_pass(self, request, protocol):
        if "Password" in request:
            if request["Password"] == self.config.adminpass:
                return True
        protocol.sendError(400, request)
        return False

    def type_ssd(self, request, reqid, protocol):
        if self.check_pass(request, protocol):
            pass

    def type_rsd(self, request, reqid, protocol):
        if self.check_pass(request, protocol):
            def callb(res):
                protocol.sendResponse({"Type": "RSD", "Server": res}, reqid)

            def errb(err):
                protocol.sendError(404, request)
            d = self.parent.add_server(request["IP"], request["Port"], request["Pin"])
            d.addCallbacks(callb, errb)

    def type_rnd(self, request, reqid, protocol):
        if self.check_pass(request, protocol):
            pass

    def type_gmt(self, request, reqid, protocol):
        if self.check_pass(request, protocol):
            def callb(res):
                protocol.sendResponse({"Type": "GMT", "Methods": res}, reqid)
            d = self.parent.get_methods()
            d.addCallback(callb)

    def type_gsc(self, request, reqid, protocol):
        if self.check_pass(request, protocol):
            def callb(res):
                jscripts = [script.to_dict() for script in res]
                protocol.sendResponse({"Type": "GSC", "Scripts": jscripts}, reqid)
            d = self.parent.get_scripts()
            d.addCallback(callb)

    def type_csc(self, request, reqid, protocol):
        if self.check_pass(request, protocol):
            def callb(res):
                protocol.sendResponse({"Type": "CSC", "Script": res.to_dict()}, reqid)
            script = Script.create_from_dict(request["Script"])
            d = self.parent.create_script(script)
            d.addCallback(callb)

    def type_esc(self, request, reqid, protocol):
        if self.check_pass(request, protocol):
            def callb(res):
                protocol.sendResponse({"Type": "ESC", "Script": res.to_dict()}, reqid)
            script = Script.create_from_dict(request["Script"])
            d = self.parent.edit_script(script)
            d.addCallback(callb)

    def type_dsc(self, request, reqid, protocol):
        if self.check_pass(request, protocol):
            def callb(res):
                protocol.sendResponse({"Type": "DSC", "ScriptId": res}, reqid)
            d = self.parent.delete_script(request["ScriptId"])
            d.addCallback(callb)

    def type_gsd(self, request, reqid, protocol):
        if self.check_pass(request, protocol):
            def callb(res):
                protocol.sendResponse({"Type": "GSD", "Servers": res}, reqid)
            d = self.parent.get_servers()
            d.addCallback(callb)

    def callMethod(self, control_server, name, **args):
        method = {"Name": name, "Fields": args}
        return self.peers[control_server].sendRequest({"Type": "CMT", "Method": method})
