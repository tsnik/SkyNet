from twisted.internet import reactor
from twisted.application import service
from MainService import MainService

a = MainService()
application = service.Application("SkyNet")
a.setServiceParent(application)
a.startService()
reactor.run()
