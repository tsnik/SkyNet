from pymlconf import ConfigManager


class Config:
    _conf = None

    @staticmethod
    def getconf():
        if Config._conf is None:
            Config._conf = ConfigManager(init_value="", files="skynet.cfg", root_file_name="skynet.cfg")
        return Config._conf
