from snp import SNPService
from Config import Config


class MainService(SNPService):
    def __init__(self):
        self.config = Config.getconf()
        self.devices = {}
        for device in self.config.devices:
            driver = getattr(__import__('drivers.{0}'.format(device.Driver), fromlist=[device.Driver]), device.Driver)
            self.devices[device.Name] = driver(self.name, self.field_updated)

    def field_updated(self, field_name, value):
        pass
