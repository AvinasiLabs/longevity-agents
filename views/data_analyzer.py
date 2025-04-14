#! python3
# -*- encoding: utf-8 -*-
"""
@Time: 2025/04/14 09:38:32
@Author: Louis Jin
@Version: 1.0
@Contact: lululouisjin@gmail.com
@Description: Data analyzer router.
"""


from fastapi import APIRouter


# local module
from customized_agent.data_analyzer.task import DataAnalyzer
from views.schema import UserRawData


router = APIRouter()
ANALYZER = DataAnalyzer()


@router.post('/recognize')
async def recognize(user_data: UserRawData):
    session_id = await ANALYZER.receive_data(
        user_data.storage_type,
        user_data.data_type,
        user_data.data_path
    )
    return {
        'result': session_id
    }


@router.get('/diagnostic/{sess_id}')
async def analyze(sess_id: str):
    result = await ANALYZER.analyze_data(sess_id)
    return result


@router.get('/questionnaire/{sess_id}')
async def analyze(sess_id: str):
    result = await ANALYZER.analyze_questionnaire(sess_id)
    return result


if __name__ == "__main__":
    ...
