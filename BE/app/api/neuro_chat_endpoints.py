from app.core.config import settings
from app.utils.logger import get_logger
from app.dtos.neuro_chat_dtos import NeuroChatResponse, GetChatResponse, MessageList

from fastapi import APIRouter, UploadFile, Form, File, Query, Path
from typing import List, Optional
import psutil

logger = get_logger("neuro_chat")

router = APIRouter(tags=["NeuroChat"])

@router.get("/getChat", response_model=GetChatResponse)
async def get_messages(user_id : str = Query(...), page_number : int = Query(...)):
    '''
        Fetches chat messages from DB
    '''
    logger.info(f"Chat History requested, User ID: {user_id}, Page Number: {page_number}")
    result : List[MessageList] = await get_messages(user_id, page_number)
    return GetChatResponse(
        status="ok",
        data=result
    )