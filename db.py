import sqlite3

# __connection = None


def get_connection(namebase: str):
    # if __connection is None:
    __connection = sqlite3.connect(namebase)
    return __connection


def init_db(force: bool = False):
    conn = get_connection("users.db")
    cur = conn.cursor()

    if force:
        cur.execute("DROP TABLE IS EXISTS users")

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
                id         INTEGER    PRIMARY KEY ASC ON CONFLICT ROLLBACK AUTOINCREMENT
                          UNIQUE,
                userid     INT (15),
                first_name TEXT,
                last_name  TEXT,
                username   TEXT,
                pass       STRING (8),
                datareg    DATETIME);""")

    conn.commit()


def init_db_passing(force: bool = False):
    conn = get_connection("users.db")
    cur = conn.cursor()

    if force:
        cur.execute("DROP TABLE IS EXISTS passing")

    cur.execute("""CREATE TABLE IF NOT EXISTS passing (
                id         INTEGER    PRIMARY KEY  AUTOINCREMENT
                          UNIQUE,
                userid     INT,
                first_name TEXT,
                last_name  TEXT,
                username   TEXT,
                datareg    DATETIME);""")

    conn.commit()


def init_db_log(force: bool = False):
    conn = get_connection("log.db")
    cur = conn.cursor()

    if force:
        cur.execute("DROP TABLE IS EXISTS log")

    cur.execute("""CREATE TABLE IF NOT EXISTS log (
        id                INTEGER  PRIMARY KEY AUTOINCREMENT,
        dt                DATETIME,
        tempatm           REAL,
        temptributary     REAL,
        tempreturn        REAL,
        condition         boolean,
        alarm             CHAR (25)
    );
     """)
    conn.commit()


def add_record(param: list):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO users(userid, first_name, last_name, username, pass, datareg) VALUES(?, ?, ?, ?, ?, ?);""",
            param)
        conn.commit()
    except Exception as err:
        pass


def add_record_passing(param: list):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO passing(userid, first_name, last_name, username, datareg) VALUES(?, ?, ?, ?, ?);""",
                    param)
        conn.commit()
    except Exception as err:
        print(err)


def add_record_log(param: list):
    conn = sqlite3.connect("log.db")
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO log (dt, tempatm, temptributary, tempreturn, condition, alarm) VALUES( ?, ?, ?, ?, ?, ?);""",
                    param)
        conn.commit()
    except Exception as err:
        print(err)


def get_record(query, param):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    rez = cur.execute(query, param)
    conn.commit()
    return rez


def get_record_passing(query, param):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    rez = cur.excute(query, param)
    conn.commit()
    return rez


def get_record_log(query, param):
    conn = sqlite3.connect("log.db")
    cur = conn.cursor()
    try:
        if param is None:
            rez = cur.execute(query)
        else:
            rez = cur.excute(query, param)
        conn.commit()
        return rez
    except Exception as err:
        return None


def shrink_log():
    conn = sqlite3.connect("log.db")
    cur = conn.cursor()
    rangeMax = 86400
    rangeNorma = 60480
    try:
        cur.execute("DELETE FROM log WHERE id < " + str(rangeMax-rangeNorma))
        conn.commit()
        cur.execute("UPDATE log SET id = log.id - " + str(rangeMax-rangeNorma-1))
        conn.commit()
        cur.execute("UPDATE sqlite_sequence SET seq = " + str(rangeNorma))
        conn.commit()
    except Exception as err:
        print(err)
    conn.close()

def shrink_passing():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    rangeMax = 3000
    rangeNorma = 1000
    try:
        cur.execute("DELETE FROM passing WHERE id < " + str(rangeMax-rangeNorma))
        conn.commit()
        cur.execute("UPDATE passing SET id = passing.id - " + str(rangeMax-rangeNorma-1))
        conn.commit()
        cur.execute("UPDATE sqlite_sequence SET seq = " + str(rangeNorma) +"WHERE name = 'passing'")
        conn.commit()
    except Exception as err:
        print(err)
    conn.close()

if __name__ == "__main__":
    init_db_passing()
