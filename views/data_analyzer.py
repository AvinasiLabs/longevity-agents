#! python3
# -*- encoding: utf-8 -*-
"""
@Time: 2025/02/15 11:06:30
@Author: Louis Jin
@Version: 1.0
@Contact: lululouisjin@gmail.com
@Description: A combination module to integrate different components for api calling
"""


import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse


router = APIRouter()


# local module
from customized_agent.data_analyzer.task import DataAnalyzer
from views.schema import ResetSession, UserRawData
from utils.logger import logger
from utils.helpers import SnowflakeIDGenerator
from utils.storage.minio_storage import MINIO_STORAGE


ID_GEN = SnowflakeIDGenerator(machine_id=os.getenv('HOST_ID', 1))


# Temporary session storage
STORAGE = dict()


@router.post('/reset')
async def reset_session(reset_sess: ResetSession):
    sess_id = reset_sess.session_id
    if not sess_id:
        sess_id = str(ID_GEN.generate_id())
    STORAGE[sess_id] = DataAnalyzer()
    return {
        'status_code': 200,
        'result': sess_id,
        'message': "This agent is developed using Peter Attia's publicly available contents and is not affiliated with or endorsed by Peter Attia."
    }


@router.post('/analyze')
async def analyze(user_data: UserRawData):
    ...


if __name__ == "__main__":
    ...
