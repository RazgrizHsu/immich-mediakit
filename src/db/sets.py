import sqlite3
from typing import Optional
from contextlib import contextmanager

from conf import envs
from util import log

lg = log.get(__name__)

@contextmanager
def mkConn():
    pathDb = envs.mkitData + 'sets.db'
    conn = sqlite3.connect(pathDb, check_same_thread=False, timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        yield conn
    finally:
        conn.close()


def close():
    return True

def init():
    with mkConn() as conn:
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
        with mkConn() as conn:
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
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("Delete From settings Where key = ?", (key,))
            c.execute("Insert Into settings (key, val) Values (?, ?)", (key, value))
            conn.commit()
            return True
    except Exception as e:
        error_msg = f"Failed to save setting value {key}: {str(e)}"
        lg.error(error_msg)
        return False
