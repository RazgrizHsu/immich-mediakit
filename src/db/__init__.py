from conf import ks, Optional
from util import log

lg = log.get(__name__)

import db.pics as pics
import db.sets as sets
import db.vecs as vecs
import db.psql as psql
import db.sim as sim


def init():
    try:
        sets.init()
        pics.init()
        vecs.init()
        psql.init()
        lg.info('All databases initialized successfully')
    except Exception as e:
        raise RuntimeError(f'Database initialization failed: {str(e)}')

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
    def __init__(self, key, cast_type=None, default=None):
        self.key = key
        self.cast_type = cast_type
        self.default = default
        self._cache_key = f'_cache_{key}'

    def __get__(self, instance, owner):
        if instance is None: return self
        if hasattr(instance, self._cache_key):
            return getattr(instance, self._cache_key)
        val = sets.get(self.key, self.default)
        if self.cast_type and val is not None:
            try:
                if self.cast_type is bool:
                    val = val.lower() in ('true', '1', 'yes', 'on') if isinstance(val, str) else bool(val)
                else:
                    val = self.cast_type(val)
            except (ValueError, TypeError):
                lg.error(f'[AutoDbField] Failed to convert {val} to {self.cast_type}, use default[{self.default}]')
                val = self.default
        setattr(instance, self._cache_key, val)
        return val

    def __set__(self, instance, value):
        if self.cast_type and value is not None:
            try:
                if self.cast_type is bool:
                    value = value.lower() in ('true', '1', 'yes', 'on') if isinstance(value, str) else bool(value)
                else:
                    value = self.cast_type(value)
            except (ValueError, TypeError):
                lg.error(f'[AutoDbField] Failed to convert {value} to {self.cast_type} for key[{self.key}], use default[{self.default}]')
                value = self.default
        sets.save(self.key, str(value))
        setattr(instance, self._cache_key, value)


class DtoSets:
    tskFloat:bool = AutoDbField('tskFloat', bool, False) #type:ignore

    usrId:Optional[str] = AutoDbField('usrId', str, '') #type:ignore

    photoQ:str = AutoDbField('photoQ', str, ks.db.thumbnail) #type:ignore
    simMin:float = AutoDbField('simMin', float, 0.93) #type:ignore
    simMax:float = AutoDbField('simMax', float, 1.00) #type:ignore

    autoNext:bool = AutoDbField('autoNext', bool, True) #type:ignore
    showGridInfo:bool = AutoDbField('showGridInfo', bool, True) #type:ignore

    simIncRelGrp:bool = AutoDbField('simIncRelGrp', bool, False) #type:ignore
    simMaxDepths:int = AutoDbField('simMaxDepths', int, 1) #type:ignore
    simMaxItems:int = AutoDbField('simMaxItems', int, 200) #type:ignore

    simCondGrpMode:bool = AutoDbField('simCondGrpMode', bool, False) #type:ignore
    simCondMaxGroups:int = AutoDbField('simCondMaxGroups', int, 10) #type:ignore
    simCondSameDate:bool = AutoDbField('simCondSameDate', bool, False) #type:ignore
    simCondSameWidth:bool = AutoDbField('simCondSameWidth', bool, False) #type:ignore
    simCondSameHeight:bool = AutoDbField('simCondSameHeight', bool, False) #type:ignore
    simCondSameSize:bool = AutoDbField('simCondSameSize', bool, False) #type:ignore

    auSel_Enable:bool = AutoDbField('autoSelectEnable', bool, True ) #type:ignore
    auSel_SkipLowSim:bool = AutoDbField('autoSelect_SkipLowSim', bool, True ) #type:ignore
    auSel_AllLivePhoto:bool = AutoDbField('autoSelect_AllLivePhoto', bool, False ) #type:ignore

    auSel_Earlier:int = AutoDbField('autoSelect_Earlier', int, 2 ) #type:ignore
    auSel_Later:int = AutoDbField('autoSelect_Later', int, 0 ) #type:ignore
    auSel_ExifRicher:int = AutoDbField('autoSelect_ExifRicher', int, 1 ) #type:ignore
    auSel_ExifPoorer:int = AutoDbField('autoSelect_ExifPoorer', int, 0 ) #type:ignore
    auSel_BiggerSize:int = AutoDbField('autoSelect_BiggerSize', int, 2 ) #type:ignore
    auSel_SmallerSize:int = AutoDbField('autoSelect_SmallerSize', int, 0 ) #type:ignore
    auSel_BiggerDimensions:int = AutoDbField('autoSelect_BiggerDimensions', int, 2 ) #type:ignore
    auSel_SmallerDimensions:int = AutoDbField('autoSelect_SmallerDimensions', int, 0 ) #type:ignore
    auSel_NameLonger:int = AutoDbField('autoSelect_NameLonger', int, 1 ) #type:ignore
    auSel_NameShorter:int = AutoDbField('autoSelect_NameShorter', int, 0 ) #type:ignore

    excl_Enable:bool = AutoDbField('exclude_Enable', bool, True ) #type:ignore
    excl_FndLess:int = AutoDbField('exclude_FindSizeLess', int, 0) #type:ignore


    @classmethod
    def get(cls, key, default=None):
        value = sets.get(key, default)
        return value

    @classmethod
    def save(cls, key, value):
        return sets.save(key, str(value))


    def clearCache(self):
        for attr_name in dir(self.__class__):
            attr = getattr(self.__class__, attr_name)
            if isinstance(attr, AutoDbField):
                cache_key = attr._cache_key
                if hasattr(self, cache_key): delattr(self, cache_key)

# global
dto = DtoSets()
