from util import log

lg = log.get(__name__)

import db.pics as pics
import db.sets as sets
import db.vecs as vecs
import db.psql as psql

# noinspection PyUnresolvedReferences
import db.dyn as dyn


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
