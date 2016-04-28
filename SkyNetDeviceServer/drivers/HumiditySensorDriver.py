from drivers.SimpleDriver import SimpleDriver
from FieldInfo import FieldInfo
from twisted.internet import defer, reactor
from twisted.protocols import basic
import serial


class HumiditySensorDriver(SimpleDriver):
    def __init__(self, did, name, updated):
        SimpleDriver.__init__(self, did, name, updated)
        self.fields = [FieldInfo("SensorData", False, 0)]
        print("Loaded")
        print(self.fields)
        p = ArduinoProtocol(self.data_recevied)
        reactor.callInThread(self.serial_reader)

    def get_device_fields(self):
        fields = {}
        for field in self.fields:
            fields[field.Name] = field
        d = defer.Deferred()
        d.callback(fields)
        return d

    def data_recevied(self, value):
        value = value.decode("utf-8")
        value = value.split(":")
        self.fields[0].Value = int(value[1])

    def serial_reader(self):
        with serial.Serial('COM4', 1200, timeout=1) as ser:
            ser.readline()
            while True:
                reactor.callFromThread(self.data_recevied, ser.readline())
