from app.core.config import settings
from app.utils.logger import get_logger
from app.dtos.neuro_chat_dtos import NeuroChatResponse, GetChatResponse, MessageList
from app.core.neuro_chat_service import get_user_messages

from fastapi import APIRouter, Query
from typing import List, Optional
import psutil

logger = get_logger("neuro_chat")

router = APIRouter(tags=["NeuroChat"])

@router.get("/getChat", response_model=GetChatResponse)
async def get_messages(user_id : str = Query(...), page_number : int = Query(1, ge=1, description="Page number starting from 1")):
    '''
        Fetches chat messages from DB
    '''
    logger.info(f"Chat History requested, User ID: {user_id}, Page Number: {page_number}")
    result : List[MessageList] = await get_user_messages(user_id, page_number)
    return GetChatResponse(
        status="ok",
        data=result
    )