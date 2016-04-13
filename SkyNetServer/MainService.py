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
        self.controlService.setServiceParent(self)
        self.deviceService.setServiceParent(self)
        self.scripts = {}

    def field_updated(self, devid, field):
        field["DevId"] = devid
        for script in self.scripts:
            script.doif(field)

    def script_load(self, res):
        self.scripts = res
        self.addService(self.controlService)
        self.addService(self.deviceService)

    def startService(self):
        service.MultiService.startService(self)
        d = DB.get_scripts()
        d.addCallback(self.script_load)

    def script_changed(self, script):
        self.scripts[script.id] = script
        return script

    def script_deleted(self, sid):
        self.scripts.pop(sid)
        return sid

    def create_script(self, script):
        d = DB.add_script(script)
        d.addCallback(self.script_changed)
        return d

    def edit_script(self, script):
        d = DB.edit_script(script)
        d.addCallback(self.script_changed)
        return d

    def delete_script(self, sid):
        d = DB.delete_script(sid)
        d.addCallback(self.script_deleted)
        return d

    def get_scripts(self):
        d = DB.get_scripts()
        d.addCallback(lambda res: res.values())
        return d

    def get_methods(self):
        d = DB.get_methods()
        return d

    def get_device_data(self, devid):
        def callb(res):
            def callb(res):
                res["DevId"] = devid
            rdevid, ip = res
            return self.deviceService.get_device_fields(ip, rdevid).addCallback(callb)
        d = DB.get_remote_device_from_local(devid)
        d.addCallback(callb)
        return d

    def update_device_field(self, devid, field, value):
        def callb(res):
            def callb(res):
                res["DevId"] = devid
            rdevid, ip = res
            return self.deviceService.update_device_field(ip, rdevid, field, value).addCallback(callb)
        d = DB.get_remote_device_from_local(devid)
        d.addCallback(callb)
        return d
