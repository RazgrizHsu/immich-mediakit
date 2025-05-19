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
    _type_hints_cache = {}
    _type_checks_cache = {}

    _cursor_columns_cache = {}  # 保存cursor的columns緩存
    _complex_type_cache = {}  # 緩存嵌套類型檢查結果

    @staticmethod
    def jsonSerializer(obj: Any) -> Any:
        if isinstance(obj, datetime): return obj.isoformat()
        return str(obj)

    # noinspection PyTypeChecker
    def toDict(self) -> Dict[str, Any]: return asdict(self)

    def toJson(self) -> str: return json.dumps(self.toDict(), default=self.jsonSerializer, ensure_ascii=False)

    def toStore(self) -> Dict[str, Any]:
        return self.toDict()

    @classmethod
    def _get_type_hints(cls):
        if cls not in BaseDictModel._type_hints_cache:
            BaseDictModel._type_hints_cache[cls] = get_type_hints(cls)
        return BaseDictModel._type_hints_cache[cls]

    @classmethod
    def _is_model_subclass(cls, type_cls):
        cache_key = (cls, type_cls)
        if cache_key not in BaseDictModel._type_checks_cache:
            result = inspect.isclass(type_cls) and issubclass(type_cls, BaseDictModel)
            BaseDictModel._type_checks_cache[cache_key] = result
        return BaseDictModel._type_checks_cache[cache_key]

    @classmethod
    def _process_typed_field(cls, key: str, val: Any, hint_type: Type) -> Any:
        if val is None:
            return None

        origin = get_origin(hint_type)

        if origin is None:
            if cls._is_model_subclass(hint_type) and isinstance(val, dict):
                return hint_type.fromStore(val)  # type: ignore
            return val

        if origin is list and isinstance(val, list):
            item_type = get_args(hint_type)[0]

            if cls._is_model_subclass(item_type):
                return [item_type.fromStore(item) for item in val]
            return val

        if origin is dict: return val

        if origin is Union:
            type_args = get_args(hint_type)
            real_types = [t for t in type_args if t is not type(None)]

            if len(real_types) == 1:
                real_type = real_types[0]
                if cls._is_model_subclass(real_type) and isinstance(val, dict):
                    return real_type.fromStore(val)
            return val

        return val

    @classmethod
    def _process_json_fields(cls, data: Dict[str, Any], type_hints: Dict[str, Type]) -> Dict[str, Any]:
        for fname, ftype in type_hints.items():
            if ftype == Json and fname in data and isinstance(data[fname], str):
                try:
                    data[fname] = Json(data[fname])
                except Exception as e:
                    raise ValueError(f"Error parsing JSON for {fname}: {str(e)}")
        return data

    @classmethod
    def _has_complex_types(cls, type_hints):
        if cls not in cls._complex_type_cache:
            complex_fields = set()
            for key, hint_type in type_hints.items():
                origin = get_origin(hint_type)
                if origin is list or origin is Union:
                    complex_fields.add(key)
                    continue

                if origin is None and cls._is_model_subclass(hint_type):
                    complex_fields.add(key)
                    continue

            cls._complex_type_cache[cls] = complex_fields

        return cls._complex_type_cache[cls]

    @classmethod
    def fromStore(cls: Type[T], src: Dict[str, Any]) -> T:
        if not src: return cls()

        type_hints = cls._get_type_hints()
        complex_fields = cls._has_complex_types(type_hints)

        if not complex_fields or not any(k in complex_fields and k in src and isinstance(src[k], (dict, list)) for k in complex_fields):
            filtered_data = {k: v for k, v in src.items() if k in type_hints}
            try:
                return cls(**filtered_data)
            except (TypeError, ValueError):
                pass

        processed_data = {}
        for key, val in src.items():
            if key not in type_hints: continue

            if key in complex_fields and (isinstance(val, dict) or isinstance(val, list)):
                processed_data[key] = cls._process_typed_field(key, val, type_hints[key])
            else:
                processed_data[key] = val

        return cls(**processed_data)

    @classmethod
    def fromDB(cls: Type[T], cursor: sqlite3.Cursor, row: tuple) -> Optional[T]:
        if not row: return None

        cursor_id = id(cursor)
        columns = cls._cursor_columns_cache.get(cursor_id)
        if columns is None:
            columns = [desc[0] for desc in cursor.description]
            cls._cursor_columns_cache[cursor_id] = columns

        data = dict(zip(columns, row))
        type_hints = cls._get_type_hints()

        json_fields = [fname for fname, ftype in type_hints.items()
                       if ftype == Json and fname in data and isinstance(data[fname], str)]

        if json_fields: data = cls._process_json_fields(data, type_hints)

        complex_fields = cls._has_complex_types(type_hints)

        complex_present = any(k in complex_fields and k in data for k in complex_fields)

        if not complex_present:
            filtered_data = {k: v for k, v in data.items() if k in type_hints}
            try:
                return cls(**filtered_data)
            except (TypeError, ValueError):
                pass

        processed_data = {}
        for key, val in data.items():
            if key not in type_hints: continue

            if key in complex_fields and (isinstance(val, dict) or isinstance(val, list)):
                processed_data[key] = cls._process_typed_field(key, val, type_hints[key])
            else:
                processed_data[key] = val

        return cls(**processed_data)
