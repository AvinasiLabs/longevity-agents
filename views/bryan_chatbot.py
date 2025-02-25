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
from customized_agent.bryan_johnson_chatbot.task import BryanChatbot
from views.schema import ResetSession, SessionChat
from utils.logger import logger
from utils.helpers import SnowflakeIDGenerator


ID_GEN = SnowflakeIDGenerator(machine_id=os.getenv('HOST_ID', 1))



# Temporary session storage
STORAGE = dict()


@router.post('/reset')
async def reset_session(reset_sess: ResetSession):
    sess_id = reset_sess.session_id
    if not sess_id:
        sess_id = str(ID_GEN.generate_id())
    STORAGE[sess_id] = BryanChatbot()
    return {
        'status_code': 200,
        'result': sess_id,
        'message': "This agent is developed using Bryan Johnson's publicly available Blueprint Protocol and is not affiliated with or endorsed by Bryan Johnson."
    }


@router.post('/bryan_johnson')
async def bryan_chat(sess_chat: SessionChat):
    sess_id = sess_chat.session_id
    if sess_id not in STORAGE:
        raise HTTPException(status_code=404, detail='Error: session_id invalid, please reset session first.')
    session: BryanChatbot = STORAGE[sess_id]
    try:
        generator = session.pipe(sess_chat.question)
        return StreamingResponse(generator, media_type='text/plain')
    except Exception as err:
        raise HTTPException(status_code=404, detail='Error: generate answer failed.')


if __name__ == "__main__":
    ...
