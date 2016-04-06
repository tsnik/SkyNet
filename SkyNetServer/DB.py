import pickle
from twisted.enterprise import adbapi


class DB:
    filename = "skynet.db"
    _db = None
    _ready = False

    @staticmethod
    def get_db():
        if DB._db is None:
            DB._db = adbapi.ConnectionPool("sqlite3", DB.filename)
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
        txn.execute('''CREATE TABLE IF NOT EXISTS Scripts
              (id INTEGER PRIMARY KEY, script TEXT)''')

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

    @staticmethod
    def get_field_value(devid, field):
        db = DB.get_db()
        return db.runInteraction(DB._get_field_value, devid, field)

    @staticmethod
    def _get_field_value(txn, devid, field):
        DB._check_db_ready()
        txn.execute('''SELECT value FROM RawData WHERE devid = ? AND field = ? ORDER BY id DESC''', devid, field)
        return txn.fetchone()[0]

    @staticmethod
    def add_script(script):
        db = DB.get_db()
        return db.runInteraction(DB._add_script, s)

    @staticmethod
    def _add_script(txn, script):
        DB._check_db_ready()
        s = pickle.dumps(script)
        txn.execute('''INSERT INTO Scripts (script) VALUES (?)''', s)
        script.id = txn.lastrowid()
        return script

    @staticmethod
    def edit_script(script):
        db = DB.get_db()
        return db.runInteraction(DB._edit_script, script)

    @staticmethod
    def _edit_script(txn, script):
        DB._check_db_ready()
        s = pickle.dumps(script)
        txn.execute('''UPDATE Scripts Set script = ? WHERE id = ?''', s, script.id)
        return script

    @staticmethod
    def get_scripts():
        db = DB.get_db()
        return db.runInteraction(DB._get_scripts)

    @staticmethod
    def _get_scripts(txn):
        DB._check_db_ready()
        txn.execute('''SELECT * FROM Scripts''')
        scripts = {}
        ss = txn.fetchall()
        for s in ss:
            scripts[s[0]] = pickle.loads(s[1])
        return scripts

    @staticmethod
    def get_id_from_ip(ip, control=False):
        db = DB.get_db()
        return db.runInteraction(DB._get_id_from_ip, ip, control)

    @staticmethod
    def _get_id_from_ip(txn, ip, control):
        DB._check_db_ready()
        if control:
            table = "ControlServers"
        else:
            table = "DeviceServers"
        txn.execute('''SELECT id FROM ? WHERE ip = ?''', table, ip)
        return txn.fetchone()[0]

    @staticmethod
    def update_devices(ip, devices):
        db = DB.get_db()
        return db.runInteraction(DB._update_devices, ip, devices)

    @staticmethod
    def _update_devices(txn, ip, devices):
        #  TODO: check if DeviceServer in db and add it if not
        pass

    @staticmethod
    def update_methods(ip, name, methods):
        db = DB.get_db()
        return db.runInteraction(DB._update_methods, ip, name, methods)

    @staticmethod
    def _update_methods(txn, ip, name, methods):
        # TODO: check if ControlServer in db and it if not
        pass

    @staticmethod
    def get_devices():
        db = DB.get_db()
        return db.runInteraction(DB._get_devices)

    @staticmethod
    def _get_devices(txn):
        DB._check_db_ready()
        txn.execute('''SELECT Devices.name, Devices.id, DeviceServers.ip, DeviceServers.name AS DeviceServerName
FROM Devices, DeviceServers WHERE Devices.device_server=DeviceServers.id''')
        res = txn.fetchall()
        devices = []
        for line in res:
            devices.append({"ID": line["id"], "Name": line["name"],
                            "SD": {"Name": line["DeviceServerName"], "IP": line["ip"]}})
        return devices
