from twisted.application import service
from DeviceService import DeviceService
from ControlService import ControlService
from Config import Config


class MainService(service.MultiService):

    def __init__(self):
        service.MultiService.__init__(self)
        self.config = Config.getconf()
        self.controlService = ControlService(self.config)
        self.deviceService = DeviceService(self.config)
        self.addService(self.controlService)
        self.addService(self.deviceService)

    def field_updated(self, devid, field):
        pass
