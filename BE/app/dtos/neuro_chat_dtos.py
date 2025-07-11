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
    message: str
    owner : ChatOwners
    timestamp : datetime


class GetChatResponse(BaseModel): 
    status : str
    data : List[MessageList]

