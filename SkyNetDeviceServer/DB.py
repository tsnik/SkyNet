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
        pass

    @staticmethod
    def _init_db_callback(res):
        DB._ready = True

    @staticmethod
    def _check_db_ready():
        while not DB._ready:
            pass