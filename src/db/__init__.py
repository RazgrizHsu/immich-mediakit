from util import log

lg = log.get(__name__)

import db.pics as pics
import db.sets as sets
import db.vecs as vecs
import db.psql as psql


def init():
    try:
        sets.init()
        pics.init()
        vecs.init()
        psql.init()
        lg.info('All databases initialized successfully')
    except Exception as e:
        lg.error(f'Database initialization failed: {str(e)}')
        return False

    return True

def close():
    try:
        sets.close()
        pics.close()
        vecs.close()
        lg.info('All database connections closed successfully')
    except Exception as e:
        lg.error(f'Failed to close database connections: {str(e)}')
        return False

    return True

def resetAllData():
    try:
        pics.clearAll()
        vecs.cleanAll()
        lg.info('[clear] All records cleared successfully')
    except Exception as e:
        lg.error(f'[clear] Failed to clear all records: {str(e)}')
        return False

    return True



class AutoDbField:
    def __init__(self, key, default=None):
        self.key = key
        self.default = default

    def __get__(self, instance, owner):
        if instance is None: return self
        return sets.get(self.key, self.default)

    def __set__(self, instance, value):
        # lg.info(f"[dynField] Saving setting k[{self.key}] v[{value}]")
        sets.save(self.key, str(value))


class DtoSets:
    usrId = AutoDbField('usrId')
    photoQ = AutoDbField('photoQ')
    simMin = AutoDbField('simMin')
    simMax = AutoDbField('simMax')

    @classmethod
    def get(cls, key, default=None):
        value = sets.get(key, default)
        return value

    @classmethod
    def save(cls, key, value):
        return sets.save(key, str(value))



# global
dto = DtoSets()
