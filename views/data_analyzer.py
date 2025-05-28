#! python3
# -*- encoding: utf-8 -*-
"""
@Time: 2025/04/14 09:38:32
@Author: Louis Jin
@Version: 1.0
@Contact: lululouisjin@gmail.com
@Description: Data analyzer router.
"""

import time
from fastapi import APIRouter, UploadFile, File


# local module
from customized_agent.data_analyzer.task import DataAnalyzer
from views.schema import UserRawData, AnanlysisRequest


router = APIRouter()
ANALYZER = DataAnalyzer()


@router.post('/recognize')
async def recognize(user_data: UserRawData):
    """Receive the data from the storage and parse it to the standard markdown format.

    Args:
        user_data (UserRawData): The request of the data.
    """
    session_id = await ANALYZER.receive_data(
        user_data.storage_type,
        user_data.data_type,
        user_data.data_path,
        user_data.user_id
    )
    return {
        'result': session_id
    }


@router.post('/diagnostic')
async def analyze(request: AnanlysisRequest):
    """Analyze the diagnostics result.

    Args:
        request (AnanlysisRequest): The request of the analysis.
    """
    result = await ANALYZER.analyze_data(request.user_id, request.sess_id)
    return result


@router.post('/questionnaire')
async def analyze(request: AnanlysisRequest):
    """Analyze the questionnaire form data.

    Args:
        request (AnanlysisRequest): The request of the analysis.
    """
    result = await ANALYZER.analyze_questionnaire(request.user_id, request.sess_id)
    return result


@router.post('/analyze')
async def analyze_file(file: UploadFile = File(...)):
    """Analyze the uploaded diagnostics raw file.

    Args:
        file (UploadFile): The uploaded diagnostics raw file.
    """
    start_time = time.time()
    file_name = file.filename
    file_type = file.content_type
    file_bytes = file.file.read()
    result = await ANALYZER.analyze_file(file_name, file_type, file_bytes)
    result = {
        'success': True,
        'data': {
            'report': result,
            'processingTime': time.time() - start_time,
            'fileInfo': {
                'name': file_name,
                'type': file_type,
                'size': len(file_bytes)
            }
        }
    }
    return result


if __name__ == "__main__":
    ...
