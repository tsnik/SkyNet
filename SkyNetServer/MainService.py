from twisted.application import service
from DeviceService import DeviceService
from ControlService import ControlService
from Config import Config
from DB import DB


class MainService(service.MultiService):

    def __init__(self):
        service.MultiService.__init__(self)
        self.config = Config.getconf()
        self.controlService = ControlService(self.config)
        self.deviceService = DeviceService(self.config)
        self.scripts = {}

    def field_updated(self, devid, field):
        pass

    def script_load(self, res):
        self.scripts = res
        self.addService(self.controlService)
        self.addService(self.deviceService)

    def startService(self):
        d = DB.get_scripts()
        d.addCallback(self.script_load)