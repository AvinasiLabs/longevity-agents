import shelve
import json
import threading
from typing import Optional, Union, List, Tuple, Any


# Local module
from configs.config_cls import ShelveConfig


class ShelveStorage:
    def __init__(self, config: ShelveConfig):
        self.config = config
        self.lock = threading.Lock()

    
    def get_items(self, obj_path: Optional[List[Union[str, int]]]=None):
        """According to the obj_path, return the object in respect of this path.

        Args:
            obj_path (Optional[List[Union[str, int]]], optional): _description_. Defaults to None.

        Returns:
            Any: shelve db object in respect of the obj_path.
        """
        with shelve.open(str(self.config.db_path)) as db:
            if obj_path:
                obj = db
                for loc in obj_path:
                    obj = obj.__getitem__(loc)
                return obj
            else:
                return list(db.keys())


    def upsert(self, key_path: Optional[List[Union[str, int]]], value: Any):
        """Upsert shelve db dict recursively by a list path and the value.
        Args:
            key_path (Optional[List[Union[str, int]]]): A list of path.
            value (Any): The value to be set.
        """
        with self.lock:
            with shelve.open(str(self.config.db_path), writeback=True) as db:
                if not key_path:
                    raise ValueError("key_path is missing")
                if len(key_path) == 1:
                    db[key_path[0]] = value
                    db.sync()
                    return
                top_key = key_path[0]
                nested_keys = key_path[1:]
                if top_key not in db:
                    db[top_key] = {}
                current = db[top_key]
                for k in nested_keys[:-1]:
                    if k not in current or not isinstance(current[k], dict):
                        current[k] = {}
                    current = current[k]
                current[nested_keys[-1]] = value
                db.sync()


    def batch_upsert(self, kv_pairs: List[Tuple[list, Any]]):
        """Upsert shelve db dict recursively by multi list path and value pairs.
        Args:
            kv_pairs (List[Tuple[list, Any]]): The multiple key_path-value pairs.
        """
        with self.lock:
            with shelve.open(str(self.config.db_path), writeback=True) as db:
                for key_path, value in kv_pairs:
                    if not key_path:
                        raise ValueError("key_path is missing")
                    if len(key_path) == 1:
                        db[key_path[0]] = value
                        db.sync()
                        continue
                    top_key = key_path[0]
                    nested_keys = key_path[1:]
                    if top_key not in db:
                        db[top_key] = {}
                    current = db[top_key]
                    for k in nested_keys[:-1]:
                        if k not in current or not isinstance(current[k], dict):
                            current[k] = {}
                        current = current[k]
                    current[nested_keys[-1]] = value
                db.sync()


    def item_list_md(self, obj_path: Optional[List[Union[str, int]]]=None):
        """Transform a List[str] or dict's keys into markdown format list as follows:
            - item 0
            - item 1
            ...

        Args:
            obj_path (Optional[List[Union[str, int]]], optional): The path to the target list. Defaults to None.
        """
        items = self.get_items(obj_path)
        if isinstance(items, dict):
            items = list(items.keys())
        items = [f'- {item}' for item in items]
        return '\n'.join(items)


class JsonStorage:
    def __init__(self, config: ShelveConfig):
        self.config = config
        self.lock = threading.Lock()

    
    def get_items(self, obj_path: Optional[List[Union[str, int]]]=None):
        """According to the obj_path, return the object in respect of this path.

        Args:
            obj_path (Optional[List[Union[str, int]]], optional): _description_. Defaults to None.

        Returns:
            Any: shelve db object in respect of the obj_path.
        """
        with open(str(self.config.db_path), 'r') as f:
            db = json.load(f)
        if obj_path:
            obj = db
            for loc in obj_path:
                obj = obj.get(loc)
            return obj
        else:
            return list(db.keys())


    def upsert(self, key_path: Optional[List[Union[str, int]]], value: Any):
        """Upsert shelve db dict recursively by a list path and the value.
        Args:
            key_path (Optional[List[Union[str, int]]]): A list of path.
            value (Any): The value to be set.
        """
        with self.lock:
            with open(str(self.config.db_path), 'r') as f:
                db = json.load(f)
            if not key_path:
                raise ValueError("key_path is missing")
            if len(key_path) == 1:
                db[key_path[0]] = value
                with open(str(self.config.db_path), 'w') as f:
                    json.dump(db, f, indent=4, ensure_ascii=False)
                return
            top_key = key_path[0]
            nested_keys = key_path[1:]
            if top_key not in db:
                db[top_key] = {}
            current = db[top_key]
            for k in nested_keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            current[nested_keys[-1]] = value
            with open(str(self.config.db_path), 'w') as f:
                json.dump(db, f, indent=4, ensure_ascii=False)


    def batch_upsert(self, kv_pairs: List[Tuple[list, Any]]):
        """Upsert shelve db dict recursively by multi list path and value pairs.
        Args:
            kv_pairs (List[Tuple[list, Any]]): The multiple key_path-value pairs.
        """
        with self.lock:
            with open(str(self.config.db_path), 'r') as f:
                db = json.load(f)
            for key_path, value in kv_pairs:
                if not key_path:
                    raise ValueError("key_path is missing")
                if len(key_path) == 1:
                    db[key_path[0]] = value
                    continue
                top_key = key_path[0]
                nested_keys = key_path[1:]
                if top_key not in db:
                    db[top_key] = {}
                current = db[top_key]
                for k in nested_keys[:-1]:
                    if k not in current or not isinstance(current[k], dict):
                        current[k] = {}
                    current = current[k]
                current[nested_keys[-1]] = value
            with open(str(self.config.db_path), 'w') as f:  
                json.dump(db, f, indent=4, ensure_ascii=False)


    def item_list_md(self, obj_path: Optional[List[Union[str, int]]]=None):
        """Transform a List[str] or dict's keys into markdown format list as follows:
            - item 0
            - item 1
            ...

        Args:
            obj_path (Optional[List[Union[str, int]]], optional): The path to the target list. Defaults to None.
        """
        items = self.get_items(obj_path)
        if isinstance(items, dict):
            items = list(items.keys())
        items = [f'- {item}' for item in items]
        return '\n'.join(items)
