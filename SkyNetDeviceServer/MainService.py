from snp import SNPService, SNProtocolServerFactory
from Config import Config
from twisted.internet import defer
from twisted.application import internet


class MainService(SNPService):
    def __init__(self):
        SNPService.__init__(self)
        self.config = Config.getconf()
        self.port = int(self.config.port)
        self.iface = self.config.iface
        self.factory = SNProtocolServerFactory(self)
        self.server = internet.TCPServer(self.port, self.factory, interface=self.iface)
        self.devices = {}
        self.num = 0
        for device in self.config.devices:
            driver = getattr(__import__('drivers.{0}'.format(device.Driver), fromlist=[device.Driver]), device.Driver)
            self.devices[self.num] = driver(self.num, device.Name, self.field_updated)
            self.num += 1
        self.getDevices()

    def startService(self):
        self.server.startService()

    def field_updated(self, device, field_name, value):
        self.peers.values()[0].sendRequest({"Type": "FCH", "DevId": device.did,
                                            "Field": {"Name": field_name, "Value": value}})

    def connectionMade(self, protocol):
        def callb(res):
            protocol.sendRequest({"Type": "WEL", "Name": self.config.name, "Devices": res})
            ip = protocol.transport.getPeer().host
            self.peers[ip] = protocol
            print("Welcome message sent")
        d = self.getDevices()
        d.addCallback(callb)

    def getDevices(self):
        def callb(res):
            devices = [{"Name": device.name, "DevId": device.did, "Fields": res[device.did]}
                       for device in self.devices.values()]
            return devices

        d = defer.gatherResults([device.get_device_fields().addCallback(
            lambda res: [field.to_dict() for field in res.values()]) for device in self.devices.values()])
        d.addCallback(callb)
        return d

    def type_gdf(self, request, reqid, protocol):
        def callb(res):
            protocol.sendResponse({"Type": "GDF", "Device": {"Name": device.name, "DevId":device.did, "Fields": res}},
                                  reqid)
        device = self.devices[request["DevId"]]
        d = device.get_device_fields().addCallback(lambda res: [field.to_dict() for field in res.values()])
        d.addCallback(callb)

    def type_udf(self, request, reqid, protocol):
        def callb(res):
            protocol.sendResponse({"Type": "UDF", "DevId": request["DevId"], "Field": res.to_dict()}, reqid)
        device = self.devices[request["DevId"]]
        d = device.update_device_field(request["Field"], request["Value"])
        d.addCallback(callb)
