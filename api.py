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
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime


# local module
from views.bryan_chatbot import router as bryan_router
from views.peter_chatbot import router as peter_router
from views.paper_chatbot import router as paper_router
from views.data_analyzer import router as analyzer_router


# API
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

app.include_router(bryan_router, prefix='/api/chatbots/bryan_johnson', tags=['bryan_chatbot'])
app.include_router(peter_router, prefix='/api/chatbots/peter_attia', tags=['peter_chatbot'])
app.include_router(paper_router, prefix='/api/chatbots/v2/longevity_paper', tags=['longevity_paper'])
app.include_router(analyzer_router, prefix='/api/analyzer/diagno_analyzer', tags=['diagno_analyzer'])


@app.get("/api/health")
async def test_get():
    return {
        "success": True,
        "data": {
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        }
    }





if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8108, workers=1)
