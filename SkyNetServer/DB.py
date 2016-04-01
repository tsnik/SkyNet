from twisted.enterprise import adbapi
class DB:
    filename = "skynet.cfg"
    _db = None
    _ready = False

    @staticmethod
    def get_db():
        if DB._db is None:
            DB._db = adbapi.ConnectionPool("sqlite3", 'skynet.db')
            d = DB._db.runInteraction(DB.init_db)
            d.addCallback(DB._init_db_callback)
        return DB._db

    @staticmethod
    def init_db(txn):
        txn.execute('''CREATE TABLE IF NOT EXISTS DeviceServers
             (id INTEGER PRIMARY KEY, ip TEXT, port INTEGER, name TEXT)''')
        txn.execute('''CREATE TABLE IF NOT EXISTS ControlServers
             (id INTEGER PRIMARY KEY, ip TEXT, name TEXT)''')
        txn.execute('''CREATE TABLE IF NOT EXISTS Methods
             (id INTEGER PRIMARY KEY, name TEXT, control_server INTEGER)''')
        txn.execute('''CREATE TABLE IF NOT EXISTS Devices
             (id INTEGER PRIMARY KEY, name TEXT, device_server INTEGER,
              device_id TEXT)''')
        txn.execute('''CREATE TABLE IF NOT EXISTS RawData
             (id INTEGER PRIMARY KEY, device INTEGER , field TEXT, value TEXT)''')

    @staticmethod
    def _init_db_callback(res):
        DB._ready = True

    @staticmethod
    def _check_db_ready():
        while not DB._ready:
            pass

    @staticmethod
    def get_device_servers():
        db = DB.get_db()
        return db.runInteraction(DB._get_device_servers)

    @staticmethod
    def _get_device_servers(txn):
        DB._check_db_ready()
        txn.execute('''SELECT * FROM DeviceServers''')
        return txn.fetchall()

    @staticmethod
    def get_local_devid_from_remote(ip, devid):
        db = DB.get_db()
        return db.runInteraction(DB._get_local_devid_from_remote, ip, devid)

    @staticmethod
    def _get_local_devid_from_remote(txn, ip, devid):
        DB._check_db_ready()
        txn.execute('''SELECT id from DeviceServers WHERE ip = ? ''', ip)
        devsid = txn.fetchone()[0]
        txn.execute('''SELECT id from Devices WHERE device_server = ? AND device_id = ?''', devsid, devid)
        return txn.fetchone()[0]
