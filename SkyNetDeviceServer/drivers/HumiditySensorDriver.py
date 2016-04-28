from drivers.SimpleDriver import SimpleDriver
from FieldInfo import FieldInfo
from twisted.internet import defer, reactor, threads
from twisted.protocols import basic
import serial


class HumiditySensorDriver(SimpleDriver):
    def __init__(self, did, name, updated):
        SimpleDriver.__init__(self, did, name, updated)
        self.fields = [FieldInfo("SensorData", False, 0), FieldInfo("Pump", True, False)]
        self.updates = []
        print("Loaded")
        print(self.fields)
        reactor.callInThread(self.serial_reader)

    def get_device_fields(self):
        fields = {}
        for field in self.fields:
            fields[field.Name] = field
        d = defer.Deferred()
        d.callback(fields)
        return d

    def update_pump(self, value):
        v = 0
        if value:
            v = 1
        self.updates.append((13, v))
        self.fields[1].Value = value;
        return self.fields[1]

    def data_recevied(self, value):
        value = value.decode("utf-8")
        value = value.split(":")
        if value[0][0] == 'A' and int(value[0][1:]) == 0:
            self.updated(self, "SensorData", int(value[1]))
            self.fields[0].Value = int(value[1])

    def get_updates(self):
        tmp = self.updates
        self.updates = []
        return tmp

    def serial_reader(self):
        with serial.Serial('COM4', 1200, timeout=1) as ser:
            while True:
                updates = threads.blockingCallFromThread(reactor, self.get_updates)
                for pin, value in updates:
                    s = "{0}:{1}\n".format(pin, value)
                    ser.write(s.encode("utf-8"))
                line = ser.readline()
                if len(line) > 0:
                    reactor.callFromThread(self.data_recevied, line)
