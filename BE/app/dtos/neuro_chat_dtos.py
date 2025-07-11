from app.dtos.error_success_codes import ErrorAndSuccessCodes
from app.dtos.collection_names import ChatOwners

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class NeuroChatResponse(BaseModel):
    """Neuro Chat response."""
    status : str
    internal_status_code : Optional[ErrorAndSuccessCodes] = None

class MessageList(BaseModel):
    """Get Chat"""
    id : str
    user_message: str
    system_message: str
    system_message_status : ErrorAndSuccessCodes
    timestamp : datetime


class GetChatResponse(BaseModel): 
    status : str
    data : List[MessageList]


class SendMessageRequest(BaseModel):
    """Send Message Request DTO"""
    user_id: str
    message: str


class SendMessageResponse(BaseModel):
    """Send Message Response DTO"""
    status: str
    message_id: str
    system_response: str
    internal_status_code: Optional[ErrorAndSuccessCodes] = None

