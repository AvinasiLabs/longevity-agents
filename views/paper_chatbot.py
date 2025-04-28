#! python3
# -*- encoding: utf-8 -*-
"""
@Time: 2025/03/10 20:37:30
@Author: Louis Jin
@Version: 1.0
@Contact: lululouisjin@gmail.com
@Description: A combination module to integrate paper chatbot components for api calling
"""


import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse


router = APIRouter()


# local module
from customized_agent.longevity_paper.task import PaperChatbot
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
    STORAGE[sess_id] = PaperChatbot()
    return {
        'status_code': 200,
        'result': sess_id,
        'message': '''Hello! 👋

I’m Longevity AI, your personal assistant for exploring the latest medical research on longevity and health. Whether you have questions about aging, life extension strategies, or insights from cutting-edge scientific papers, I’m here to help!

Ask me anything about longevity, and I’ll provide answers based on peer-reviewed research. Let’s unlock the secrets to a longer, healthier life together!

Disclaimer: The information I provide is based on scientific studies and should not be considered as medical advice. Always consult with a healthcare professional before making any decisions related to your health and well-being.'''
    }


@router.post('/chat')
async def paper_chat(sess_chat: SessionChat):
    sess_id = sess_chat.session_id
    if sess_id not in STORAGE:
        raise HTTPException(status_code=404, detail='Error: session_id invalid, please reset session first.')
    session: PaperChatbot = STORAGE[sess_id]
    try:
        generator = session.pipe(sess_chat.question, sess_id)
        return StreamingResponse(generator, media_type='text/plain')
    except Exception as err:
        raise HTTPException(status_code=404, detail='Error: generate answer failed.')


if __name__ == "__main__":
    ...
