import inspect
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional, Type, TypeVar, Union, get_type_hints, get_origin, get_args

from util import log

lg = log.get(__name__)

T = TypeVar('T', bound='BaseDictModel')

class Json(Dict[str, Any]):
    def __init__(self, data=None):
        super().__init__()
        if data:
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception as e:
                    raise ValueError(f"Error parsing JSON string: {e}")

            if isinstance(data, dict):
                for k, v in data.items():
                    if v == 'null':
                        self[k] = None
                    else:
                        self[k] = v


# noinspection PyArgumentList
@dataclass
class BaseDictModel:

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        if isinstance(obj, datetime): return obj.isoformat()
        return str(obj)

    # noinspection PyTypeChecker
    def toDict(self) -> Dict[str, Any]: return asdict(self)

    def toJson(self) -> str: return json.dumps(self.toDict(), default=self._json_serializer, ensure_ascii=False)

    def toStore(self) -> Dict[str, Any]:
        return self.toDict()


    @classmethod
    def fromStore(cls: Type[T], src: Dict[str, Any]) -> T:
        # lg.info( f"[BaseDictModel] {cls.__name__}.fromStore: ({type(data)}){data}" )

        type_hints = get_type_hints(cls)

        data = {}

        for key, val in src.items():
            if key not in type_hints:
                data[key] = val
                continue

            hint_type = type_hints[key]
            origin = get_origin(hint_type)

            if origin is list:
                item_type = get_args(hint_type)[0]

                if inspect.isclass(item_type) and issubclass(item_type, BaseDictModel) and isinstance(val, list):
                    data[key] = [item_type.fromStore(item) for item in val]
                else:
                    data[key] = val

            elif origin is dict: 
                data[key] = val

            # 處理 Union/Optional 型別 (Optional 實際上是 Union[T, None])
            elif origin is Union:
                type_args = get_args(hint_type)
                # 找出不是 None 的型別
                real_types = [t for t in type_args if t is not type(None)]
                
                if len(real_types) == 1:
                    real_type = real_types[0]
                    if inspect.isclass(real_type) and issubclass(real_type, BaseDictModel) and isinstance(val, dict):
                        data[key] = real_type.fromStore(val)
                    else:
                        data[key] = val
                else:
                    # 複雜的 Union 型別，無法處理，直接賦值
                    data[key] = val
                    
            elif inspect.isclass(hint_type) and issubclass(hint_type, BaseDictModel) and isinstance(val, dict):
                data[key] = hint_type.fromStore(val)

            else:
                data[key] = val

        return cls(**data)

    @classmethod
    def fromDB(cls: Type[T], cursor: sqlite3.Cursor, row: tuple) -> Optional[T]:
        if not row: return None

        # cursor to dict
        columns = [desc[0] for desc in cursor.description]
        data = {columns[i]: row[i] for i in range(len(columns))}

        type_hints = get_type_hints(cls)

        for fname, ftype in type_hints.items():
            if ftype == Json and fname in data and isinstance(data[fname], str):
                try:
                    data[fname] = Json(data[fname])
                except Exception as e:
                    raise ValueError(f"Error parsing JSON for {fname}: {str(e)}")

        return cls.fromStore(data)
