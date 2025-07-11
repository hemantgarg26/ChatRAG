from app.core.config import settings
from app.utils.logger import get_logger
from app.dtos.neuro_chat_dtos import NeuroChatResponse, GetChatResponse, MessageList, SendMessageRequest, SendMessageResponse
from app.core.neuro_chat_service import get_user_messages, send_message_to_system

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

@router.post("/sendMessage", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    '''
        Sends a message to the system and returns system response
    '''
    logger.info(f"Message sending requested, User ID: {request.user_id}, Message: {request.message}")
    result: SendMessageResponse = await send_message_to_system(request)
    return result