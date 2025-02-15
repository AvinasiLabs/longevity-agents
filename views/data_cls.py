from typing import Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, ConfigDict, Field



class BaseRequest(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid")

    session_id: int


# Request BaseModel class
class ResetSession(BaseRequest):
    session_id: int = None


class SessionChat(BaseRequest):
    question: str = ''
    file_bs64: str = None