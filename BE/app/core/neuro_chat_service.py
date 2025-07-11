from app.dtos.error_success_codes import ErrorAndSuccessCodes
from app.dtos.collection_names import ChatOwners, CollectionNames
from app.utils.db_query import MongoQueryApplicator
from app.utils.logger import get_logger
from app.dtos.neuro_chat_dtos import MessageList
from app.core.config import settings

from typing import List
from bson import ObjectId
from datetime import datetime

logger = get_logger("neuro_chat_service")


async def get_user_messages(user_id, page_number) -> List[MessageList]: 
    try:
        # First, validate if user exists
        query = {"_id" : ObjectId(user_id)}
        mongo = MongoQueryApplicator(CollectionNames.USERS.value)
        users = await mongo.find(query)
        print("users", users)
        if not users or len(users) == 0:
            logger.info(f"No User Found User Id : {user_id}")
            return []
        
        # Fetch chat messages for the user with pagination
        messages_per_page = settings.MESSAGES_PER_PAGE
        skip = (page_number - 1) * messages_per_page
        
        # Query chat messages for the user
        chat_query = {"user_id": ObjectId(user_id)}
        chat_mongo = MongoQueryApplicator(CollectionNames.CHAT.value)
        
        # Fetch messages with pagination and sorting (ascending order by timestamp)
        chat_messages = await chat_mongo.find_paginated(
            filters=chat_query,
            skip=skip,
            limit=messages_per_page,
            sort_field="timestamp",
            sort_order=1  # 1 for ascending (oldest first)
        )
        
        # Transform database documents to MessageList DTOs
        res: List[MessageList] = []
        for message in chat_messages:
            message_dto = MessageList(
                id=str(message["_id"]),
                user_message=message.get("user_message", ""),
                system_message=message.get("system_message", ""),
                system_message_status=message.get("system_message_status", ErrorAndSuccessCodes.SUCCESS),
                timestamp=message.get("timestamp", datetime.utcnow())
            )
            res.append(message_dto)
        
        logger.info(f"Successfully fetched {len(res)} messages for user {user_id}, page {page_number}")
        return res
        
    except Exception as e:
        logger.error(f"Error while fetching messages: {e}, USER ID: {user_id}, PAGE NUMBER: {page_number}")
        return []