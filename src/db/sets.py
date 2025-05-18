import os
import sqlite3
from typing import Optional

from conf import envs
from util import log

lg = log.get(__name__)
conn: Optional[sqlite3.dbapi2.Connection] = None

def getConn():
    global conn
    if conn is None: conn = sqlite3.connect(envs.mkitData + 'sets.db', check_same_thread=False)
    return conn


def close():
    global conn
    try:
        if conn is not None: conn.close()
        conn = None
        return True
    except Exception as e:
        lg.error(f"Failed to close database connection: {str(e)}")
        return False

def init():
    global conn
    os.makedirs(envs.mkitData, exist_ok=True)

    conn = getConn()
    c = conn.cursor()

    c.execute('''
		Create Table If Not Exists settings (
		   key TEXT Primary Key,
		   val TEXT
		)
''')

    conn.commit()

def get(key, defaultValue=None):
    try:
        conn = getConn()
        c = conn.cursor()

        c.execute("Select val From settings Where key = ?", (key,))
        result = c.fetchone()

        value = result[0] if result else defaultValue
        return value
    except Exception as e:
        error_msg = f"Failed to get setting value {key}: {str(e)}"
        lg.error(error_msg)
        return defaultValue


def save(key, value):
    try:
        conn = getConn()
        c = conn.cursor()

        c.execute("Delete From settings Where key = ?", (key,))
        c.execute("Insert Into settings (key, val) Values (?, ?)", (key, value))

        conn.commit()
        return True
    except Exception as e:
        error_msg = f"Failed to save setting value {key}: {str(e)}"
        lg.error(error_msg)
        return False
