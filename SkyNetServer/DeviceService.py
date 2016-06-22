from snp import SNPService, SNProtocolClientFactory, CertManager
from DB import DB
from twisted.internet import defer
from twisted.python import failure


class DeviceService(SNPService):

    def __init__(self, config):
        SNPService.__init__(self)
        self.config = config
        self.connecting_servers = {}
        self.cert_manager = CertManager("keys", "device_servers", self.config.name)

    def startService(self):
        def callb(res):
            for dev in res:
                fact = SNProtocolClientFactory(self)
                self.cert_manager.connect_to_server(dev[1], dev[2], fact)
        DB.get_device_servers().addCallback(callb)

    def type_fch(self, request, reqid, protocol):
        ip = protocol.transport.getPeer().host

        def callb(res):
            protocol.sendResponse(request, reqid)
            self.parent.field_updated(res, request["Field"])
        DB.get_local_devid_from_remote(ip, request["DevId"]).addCallback(callb)

    def type_aur(self, request, reqid, protocol):
        #  TODO: request to control server for device server pass
        pass

    def type_wel(self, request, reqid, protocol):
        def callb(res, ip):
            protocol.sendResponse({"Name": self.config.name}, reqid)
            if ip in self.connecting_servers:
                self.connecting_servers[ip].callback(res)
        ip = protocol.transport.getPeer().host
        port = protocol.transport.getPeer().port
        self.peers[ip] = protocol
        DB.update_devices(ip, port, request["Name"], request["Devices"]).addCallback(callb, ip)

    def get_device_fields(self, device_server, devid):
        return self.peers[device_server].sendRequest({"Type": "GDF", "DevId": devid})

    def update_device_field(self, device_server, devid, field, value):
        return self.peers[device_server].sendRequest({"Type": "UDF", "DevId": devid,
                                                      "Field": field, "Value": value})

    def add_server(self, ip, port, pin):
        fact = SNProtocolClientFactory(self)
        self.cert_manager.connect_to_server(ip, port, fact)
        d = defer.Deferred()
        self.connecting_servers[ip] = d
        return d

    def clientConnectionFailed(self, connector, reason):
        ip = connector.getDestination().host
        if ip in self.connecting_servers:
            self.connecting_servers[ip].errback(Exception(ip))