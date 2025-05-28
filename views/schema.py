from typing import Optional, Union, Literal, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, ConfigDict, Field
from fastapi import UploadFile


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
    data_type: str
    data_path: str
    user_id: str


class AnanlysisRequest(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid")

    user_id: str
    sess_id: str
