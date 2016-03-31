from snp.SNPService import SNPService


class DeviceService(SNPService):

    def __init__(self, config):
        self.config = config

    def startService(self):
        #TODO: connect to all deviceServers fom db
        pass

    def connectionMade(self, protocol):
        pass
