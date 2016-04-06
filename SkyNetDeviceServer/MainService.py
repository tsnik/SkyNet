from snp import SNPService
from Config import Config


class MainService(SNPService):
    def __init__(self):
        self.config = Config.getconf()
        self.devices = {}