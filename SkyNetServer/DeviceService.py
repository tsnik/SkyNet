from snp import SNPService, SNProtocolClientFactory
from DB import DB


class DeviceService(SNPService):

    def __init__(self, config):
        SNPService.__init__(self)
        self.config = config

    def startService(self):
        def callb(res):
            from twisted.internet import reactor
            for dev in res:
                fact = SNProtocolClientFactory(self)
                reactor.connectTCP(dev[1], dev[2], fact)
        DB.get_device_servers().addCallback(callb)

    def type_fch(self, request, reqid, protocol):
        ip = protocol.transport.getPeer().host

        def callb(res):
            self.parent.field_updated(res, request["Field"])
        DB.get_local_devid_from_remote(ip, request["DevId"]).addCallback(callb)

    def type_aur(self, request, reqid, protocol):
        #  TODO: request to control server for device server pass
        pass

    def type_wel(self, request, reqid, protocol):
        def callb(res):
            protocol.sendResponse({"Name": self.config.name}, reqid)
        ip = protocol.transport.getPeer().host
        self.peers[ip] = protocol
        DB.update_devices(ip, request["Name"], request["Devices"]).addCallback(callb)

    def get_device_fields(self, device_server, devid):
        return self.peers[device_server].sendRequest({"Type": "GDF", "DevId": devid})

    def update_device_field(self, device_server, devid, field, value):
        return self.peers[device_server].sendRequest({"Type": "UDF", "DevId": devid,
                                                      "FieldName": field, "Value": value})
