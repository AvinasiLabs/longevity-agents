#! python3
# -*- encoding: utf-8 -*-
"""
@Time: 2024/04/16 13:29:16
@Author: Louis
@Version: 1.0
@Contact: lululouisjin@gmail.com
@Description: Some useful helper classes and functions.
"""


import os
import yaml
import hashlib
import asyncio
import threading
import time
import base64
from dotenv import load_dotenv


load_dotenv()


# metaclass singleton used for singleton instance
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # we have not every built an instance before.  Build one now.
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        else:
            instance = cls._instances[cls]
            # here we are going to call the __init__ and maybe reinitialize.
            if (
                hasattr(cls, "__allow_reinitialization")
                and cls.__allow_reinitialization
            ):
                # if the class allows reinitialization, then do it
                instance.__init__(*args, **kwargs)  # call the init again
        return instance


# use yaml to load config and env variables
def env_var_constructor(loader, node):
    value = loader.construct_scalar(node)
    var_name = value.strip("${}")
    return os.getenv(var_name, value)


yaml.SafeLoader.add_constructor("!env", env_var_constructor)


def open_yaml_config(config_path):
    with open(config_path, "r") as f:
        base_config = yaml.safe_load(f)
    return base_config


def gen_md5(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def get_proxies(is_static=True, host="127.0.0.1", port=26003, api=""):
    if is_static:
        return {"http": f"http://{host}:{port}", "https": f"http://{host}:{port}"}
    else:
        raise NotImplementedError("Unsupported proxy type.")


def get_proxy(is_static=True, host="127.0.0.1", port=26003, api=""):
    if is_static:
        return f"http://{host}:{port}"
    else:
        raise NotImplementedError("Unsupported proxy type.")


def dfs(dict_obj: dict, tgt_key):
    tgt_value = None
    for k, v in dict_obj.items():
        if k == tgt_key:
            return v
        elif isinstance(v, dict):
            tgt_value = dfs(v, tgt_key)
            if tgt_value is not None:
                return tgt_value
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    tgt_value = dfs(item, tgt_key)
                    if tgt_value is not None:
                        return tgt_value
    return tgt_value


def atimer(func):
    async def wrapper(*args, **kwargs):
        st = time.time()
        result = await func(*args, **kwargs)
        et = time.time()
        print(f'协程 {func.__name__} 运行时间： {et - st}')
        return result
    return wrapper

def b64_to_bytes(b64_data:str, encoding="utf-8"):
    return base64.b64decode(b64_data.encode(encoding))


def bytes_to_b64(bytes_data:bytes, encoding="utf-8"):
    return base64.b64encode(bytes_data).decode(encoding)


generate_md5 = lambda text: hashlib.md5(text.encode('utf-8')).hexdigest()


class SnowflakeIDGenerator:
    def __init__(self, machine_id):
        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

        # Bits allocation
        self.timestamp_bits = 41
        self.machine_id_bits = 10
        self.sequence_bits = 12

        # Max values
        self.max_machine_id = (1 << self.machine_id_bits) - 1
        self.max_sequence = (1 << self.sequence_bits) - 1

        # Shifts
        self.timestamp_shift = self.machine_id_bits + self.sequence_bits
        self.machine_id_shift = self.sequence_bits

        if self.machine_id > self.max_machine_id or self.machine_id < 0:
            raise ValueError(f"Machine ID must be between 0 and {self.max_machine_id}")

    def _current_timestamp(self):
        return int(time.time() * 1000)

    def _wait_for_next_millisecond(self, last_timestamp):
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    def generate_id(self):
        with self.lock:
            timestamp = self._current_timestamp()

            if timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards. Refusing to generate ID.")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    timestamp = self._wait_for_next_millisecond(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            id = ((timestamp << self.timestamp_shift) |
                  (self.machine_id << self.machine_id_shift) |
                  self.sequence)
            return id


class AsyncDict:
    def __init__(self, max_size):
        self.max_size = max_size
        self._dict = dict()
        self.lock = asyncio.Lock()  # 用于线程安全
        self.not_full = asyncio.Condition(self.lock)  # 用于等待字典未满

    async def put(self, key, value):
        async with self.lock:
            # 如果字典已满，等待直到有空间
            while len(self._dict) >= self.max_size:
                print(f"Dictionary is full. Waiting to insert ({key}, {value})...")
                await self.not_full.wait()  # 阻塞等待

            # 插入新键值对
            self._dict[key] = value
            print(f"Inserted ({key}, {value}). Dictionary: {self._dict}")

    async def remove(self, key):
        async with self.lock:
            if key in self._dict:
                # 移除键值对
                del self._dict[key]
                print(f"Removed key: {key}. Dictionary: {self._dict}")
                # 通知等待的协程字典未满
                self.not_full.notify_all()
            else:
                print(f"Key {key} not found in dictionary.")

    async def get(self, key):
        async with self.lock:
            return self._dict.get(key)


    async def pop(self, key, default=None):
        async with self.lock:
            result = self._dict.pop(key, default)
            self.not_full.notify_all()
        return result

    def __contains__(self, key):
        return key in self._dict

    def __len__(self):
        return len(self._dict)

    def __repr__(self):
        return repr(self._dict)


if __name__ == "__main__":
    ...
