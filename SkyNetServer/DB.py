import pickle
import json
import sqlite3
from twisted.enterprise import adbapi


class DB:
    filename = "skynet.db"
    _db = None
    _ready = False

    @staticmethod
    def get_db():
        if DB._db is None:
            def callb(con):
                con.row_factory = sqlite3.Row
            DB._db = adbapi.ConnectionPool("sqlite3", DB.filename, cp_openfun=callb)
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
              (id INTEGER PRIMARY KEY, name TEXT, Arguments TEXT, control_server INTEGER)''')
        txn.execute('''CREATE TABLE IF NOT EXISTS Devices
              (id INTEGER PRIMARY KEY, name TEXT, device_server INTEGER,
              device_id TEXT)''')
        txn.execute('''CREATE TABLE IF NOT EXISTS RawData
              (id INTEGER PRIMARY KEY, device INTEGER , field TEXT,
               value TEXT, date INTEGER DEFAULT (strftime('%s')))''')
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
        txn.execute('''SELECT id from DeviceServers WHERE ip = ? ''', (ip,))
        devsid = txn.fetchone()[0]
        txn.execute('''SELECT id from Devices WHERE device_server = ? AND device_id = ?''', (devsid, devid))
        return txn.fetchone()[0]

    @staticmethod
    def get_field_value(devid, field):
        db = DB.get_db()
        return db.runInteraction(DB._get_field_value, devid, field)

    @staticmethod
    def _get_field_value(txn, devid, field):
        DB._check_db_ready()
        txn.execute('''SELECT value FROM RawData WHERE devid = ? AND field = ? ORDER BY id DESC''', (devid, field))
        return txn.fetchone()[0]

    @staticmethod
    def add_script(script):
        db = DB.get_db()
        return db.runInteraction(DB._add_script, script)

    @staticmethod
    def _add_script(txn, script):
        DB._check_db_ready()
        s = pickle.dumps(script)
        txn.execute('''INSERT INTO Scripts (script) VALUES (?)''', (s,))
        script.id = txn.lastrowid
        DB._edit_script(txn, script)
        return script

    @staticmethod
    def edit_script(script):
        db = DB.get_db()
        return db.runInteraction(DB._edit_script, script)

    @staticmethod
    def _edit_script(txn, script):
        DB._check_db_ready()
        s = pickle.dumps(script)
        txn.execute('''UPDATE Scripts Set script = ? WHERE id = ?''', (s, script.id))
        return script

    @staticmethod
    def delete_script(sid):
        db = DB.get_db()
        return db.runInteraction(DB._delete_script, sid)

    @staticmethod
    def _delete_script(txn, sid):
        DB._check_db_ready()
        txn.execute('''DELETE FROM Scripts WHERE id = ?''', (sid,))
        return sid

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
    def update_devices(ip, port, name, devices):
        db = DB.get_db()
        return db.runInteraction(DB._update_devices, ip, port, name, devices)

    @staticmethod
    def _update_devices(txn, ip, port, name, devices):
        DB._check_db_ready()
        txn.execute('''SELECT * FROM DeviceServers WHERE ip = ?''', (ip,))
        server = txn.fetchone()
        if server is None:
            txn.execute('''INSERT INTO DeviceServers (ip, port, name) VALUES (?, ?, ?)''', (ip, port, name))
            cid = txn.lastrowid
            txn.execute('''SELECT * FROM DeviceServers WHERE ip = ?''', (ip,))
            server = txn.fetchone()
        else:
            cid = server["id"]
        for device in devices:
            name = device["Name"]
            txn.execute('''SELECT id FROM Devices WHERE device_server = ? and name = ?''', (cid, name))
            r = txn.fetchone()
            if r is None:
                txn.execute("INSERT INTO Devices (name, device_server, device_id) VALUES (?, ?, ?)",
                            (name, cid, device["DevId"]))
                did = txn.lastrowid
            else:
                did = r["id"]
                txn.execute("UPDATE Devices SET device_id = ? WHERE id = ?", (device["DevId"], did))
            for field in device["Fields"]:
                txn.execute('''INSERT INTO RawData (device, field, value) VALUES (?, ?, ?)''',
                            (did, field["Name"], field["Value"]))
        return server

    @staticmethod
    def update_methods(ip, name, methods):
        db = DB.get_db()
        return db.runInteraction(DB._update_methods, ip, name, methods)

    @staticmethod
    def _update_methods(txn, ip, name, methods):
        DB._check_db_ready()
        txn.execute('''SELECT id FROM ControlServers WHERE ip = ?''', (ip,))
        r = txn.fetchone()
        if r is None:
            txn.execute('''INSERT INTO ControlServers (ip, name) VALUES (?, ?)''', (ip, name))
            cid = txn.lastrowid
        else:
            cid = r["id"]
        for method in methods:
            name = method["Name"]
            args = json.dumps(method["Fields"])
            txn.execute('''SELECT id FROM Methods WHERE control_server = ?, name = ?''', (cid, name))
            r = txn.fetchone()
            if r is None:
                txn.execute("INSERT INTO Methods (name, arguments, control_server) VALUES (?, ?, ?)", (name, args, cid))
            else:
                mid = r["id"]
                txn.execute("UPDATE Methods SET arguments = ? WHERE id = ?", (args, mid))
        return

    @staticmethod
    def get_methods():
        db = DB.get_db()
        return db.runInteraction(DB._get_methods)

    @staticmethod
    def _get_methods(txn):
        DB._check_db_ready()
        txn.execute('''SELECT Methods.id, Methods.name, Methods.arguments,
        ControlServers.name as ControlName, ControlServers.ip as ControlIp
        WHERE Methods.control_server = ControlServers.id''')
        methods = txn.fetchall()
        mres = []
        for method in methods:
            tmp = {"MethodId": method['id'], "Name": method['name'], "Fields": json.loads(method["arguments"]),
                   "SD": {"Name": method["ControlName"],
                          "IP": method["ControlIp"]}}
            mres.append(tmp)
        return mres

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

    @staticmethod
    def get_remote_device_from_local(devid):
        db = DB.get_db()
        return db.runInteraction(DB._get_remote_device_from_local, devid)

    @staticmethod
    def _get_remote_device_from_local(txn, devid):
        DB._check_db_ready()
        txn.execute('''SELECT Devices.device_id as DevId, DeviceServers.ip From Devices, DeviceServers
                    WHERE Devices.device_server = DeviceServers.id AND Devices.id = ?''', str(devid))
        r = txn.fetchone()
        return int(r["DevId"]), r["ip"]
