from typing import Optional, Union, Literal, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, ConfigDict, Field



class BaseRequest(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid")

    session_id: str


# Request BaseModel class
class ResetSession(BaseRequest):
    session_id: str = None


class SessionChat(BaseRequest):
    question: str = ''
    file_bs64: str = None


class UserRawData(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid")

    storage_type: Literal['minio', 'ipfs']
    data_type: Literal['text', 'pdf', 'img']
    data_path: str
