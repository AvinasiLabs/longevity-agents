#! python3
# -*- encoding: utf-8 -*-
"""
@Time: 2024/04/03 16:54:30
@Author: Louis
@Version: 1.0
@Contact: lululouisjin@gmail.com
@Description: 
"""


import uvicorn
from fastapi import FastAPI


# local module
from views.chatbot import router as chatbot_router


# API
app = FastAPI()

app.include_router(chatbot_router, prefix='/chatbots', tags=['chatbots'])


@app.get("/test_get")
async def test_get():
    return {"message": "Welcome to the API"}



if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=20770, workers=1)
