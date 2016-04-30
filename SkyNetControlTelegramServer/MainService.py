from snp import SNPService, SNProtocolClientFactory, Script, CertManager
from Config import Config
from twisted.internet import reactor, ssl
from TelegramService import TelegramService


class MainService(SNPService):
    def __init__(self):
        SNPService.__init__(self)
        self.config = Config.getconf()
        self.name = self.config.name
        self.port = int(self.config.server.Port)
        self.ip = self.config.server.IP
        self.tg = TelegramService(self.config.token)
        self.cert_manager = CertManager("keys", "skynet", self.name)

    def type_wel(self, request, reqid, protocol):
        protocol.sendResponse({"Type": "WEL", "Name": self.name, "Methods": []}, reqid)

    def type_cmt(self, request, reqid, protocol):
        pass

    def startService(self):
        from snp import create_self_signed_cert
        create_self_signed_cert("keys", self.config.name)
        fact = SNProtocolClientFactory(self)
        self.cert_manager.connect_to_server(self.ip, self.port, fact)
        //reactor.connectSSL(self.ip, self.port, fact, ssl.ClientContextFactory())

        self.tg.parent = self
        self.tg.startService()

    def connectionMade(self, protocol):
        ip = protocol.transport.getPeer().host
        self.peers[ip] = protocol

    def get_devices(self):
        def callb(res):
            ret = {}
            devices = res["Devices"]
            for device in devices:
                ret[int(device["ID"])] = device["Name"]
            return ret
        d = list(self.peers.values())[0].sendRequest({"Type": "GDL"})
        d.addCallback(callb)
        return d

    def get_device_info(self, id):
        def callb(res):
            return res["Device"]
        d = list(self.peers.values())[0].sendRequest({"Type": "GDF", "DevId": id})
        d.addCallback(callb)
        return d

    def get_scripts(self, password):
        def callb(res):
            scripts = {int(script["Id"]): Script.create_from_dict(script)for script in res["Scripts"]}
            return scripts
        d = list(self.peers.values())[0].sendRequest({"Type": "GSC", "Password": password})
        d.addCallback(callb)
        return d

    def remove_script(self, id, password):
        d = list(self.peers.values())[0].sendRequest({"Type": "DSC", "ScriptId": id, "Password": password})
        return d

    def update_field(self, dev_id, field, value):
        d = list(self.peers.values())[0].sendRequest({"Type": "UDF",
                                                      "DevId": dev_id, "Field": field, "Value": value})
        return d

    def create_script(self, script, password):
        d = list(self.peers.values())[0].sendRequest({"Type": "CSC", "Script": script.to_dict(), "Password": password})
        return d

    def get_servers(self, password):
        def callb(res):
            return res["Servers"]
        d = list(self.peers.values())[0].sendRequest({"Type": "GSD", "Password": password})
        d.addCallback(callb)
        return d

    def add_server(self, ip, port, pin, password):
        def callb(res):
            return res["Server"]
        d = list(self.peers.values())[0].sendRequest({"Type": "RSD", "Password": password,
                                                      "IP": ip, "Port": port, "Pin": pin})
        d.addCallback(callb)
        return d
