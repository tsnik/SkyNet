from drivers.SimpleDriver import SimpleDriver
from FieldInfo import FieldInfo
from twisted.internet import defer, reactor, threads
from twisted.protocols import basic
import serial


class HumiditySensorDriver(SimpleDriver):
    def __init__(self, did, name, updated):
        SimpleDriver.__init__(self, did, name, updated)
        self.fields = [FieldInfo("SensorData", False, 0), FieldInfo("Pump", True, False),
                       FieldInfo("Interval", True, 1), FieldInfo("TimeOut", True, 3600),
                       FieldInfo("ManualPump", True, False)]
        self.updates = []
        self.interval = 1
        self.timeout = 3600
        self.active = True
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
        if self.active or not value:
            v = 0
            if value and self.active:
                v = 1
            self.updates.append((13, v))
            self.fields[1].Value = value
            self.fields[4].Value = value
            self.active = False
            reactor.callLater(self.interval, self.update_pump, False)
            reactor.callLater(self.timeout, self.activate)
        return self.fields[1]

    def update_manualpump(self, value):
        v = 0
        if value:
            v = 1
        self.updates.append((13, v))
        self.fields[1].Value = value
        self.fields[4].Value = value
        return self.fields[4]


    def activate(self):
        self.active = True

    def update_interval(self, value):
        self.interval = value
        self.fields[2].Value = value
        return self.fields[2]

    def update_timeout(self, value):
        self.active = True
        self.timeout = value
        self.fields[3].Value = value
        return self.fields[3]

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
