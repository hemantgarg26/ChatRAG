from app.dtos.error_success_codes import ErrorAndSuccessCodes
from app.dtos.collection_names import ChatOwners, CollectionNames
from app.utils.db_query import MongoQueryApplicator
from app.utils.logger import get_logger
from app.dtos.neuro_chat_dtos import MessageList, SendMessageRequest, SendMessageResponse, GetMessagesStatusRequest, GetMessagesStatusResponse, MessageStatus
from app.core.config import settings
from app.core.worker import process_message_task 
from app.utils.generic_utils import convert_string_ids_to_object_ids

from typing import List
from bson import ObjectId
from datetime import datetime
import asyncio
import uuid

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

async def send_message_to_system(request: SendMessageRequest) -> SendMessageResponse:
    """
    Process user message by saving it to the chats collection and sending to Celery for processing.
    Args:
        request (SendMessageRequest): Contains user_id and message
    Returns:
        SendMessageResponse: Response containing message_id and status
    """
    mongo = None
    message_id = None
    
    try:
        # First, validate if user exists
        user_query = {"_id": ObjectId(request.user_id)}
        user_mongo = MongoQueryApplicator(CollectionNames.USERS.value)
        users = await user_mongo.find(user_query)
        
        if not users or len(users) == 0:
            logger.info(f"No User Found User Id : {request.user_id}")
            return SendMessageResponse(
                status="error",
                message_id="",
                system_response="User not found",
                internal_status_code=ErrorAndSuccessCodes.INVALID_INPUT
            )
        
        # Save user message to chats collection
        mongo = MongoQueryApplicator(CollectionNames.CHAT.value)
        message_id = await mongo.insert_one({
            'user_id': ObjectId(request.user_id),
            'user_message': request.message,
            'system_message': "",
            'system_message_status': ErrorAndSuccessCodes.MESSAGE_UNDER_PROCESSING.value,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })
        
        logger.info(f"Message saved to database with ID: {message_id} for user: {request.user_id}")
        
        # Send to Celery task queue for processing
        CeleryTaskQueue().process_message(message_id)
        
        return SendMessageResponse(
            status="success",
            message_id=str(message_id),
            system_response="Message received and is being processed",
            internal_status_code=ErrorAndSuccessCodes.SUCCESS
        )
        
    except Exception as e:
        logger.error(f"Error while processing message: {e}, USER ID: {request.user_id}")        
        # Update message status to failed if it was created
        if mongo and message_id:
            try:
                await mongo.update_one(
                    {"_id": ObjectId(message_id)},
                    {
                        'system_message_status': ErrorAndSuccessCodes.PROCESSING_ERROR.value,
                        'system_message': "Error processing message"
                    }
                )
            except Exception as update_error:
                logger.error(f"Error updating message status: {update_error}")
        
        return SendMessageResponse(
            status="error",
            message_id=str(message_id) if message_id else "",
            system_response="Sorry, I encountered an error processing your message. Please try again.",
            internal_status_code=ErrorAndSuccessCodes.PROCESSING_ERROR
        )


class CeleryTaskQueue:
    def process_message(self, message_id):
        return process_message_task.delay(message_id)
    
async def get_messages_status(request: GetMessagesStatusRequest) -> GetMessagesStatusResponse:
    '''
        Get status of messages
    '''
    logger.info(f"Message statusses requested, User ID: {request.user_id}, Message IDS: {request.message_ids}")
    res = []

    if not request.message_ids or not request.user_id:
        logger.error(f"Invalid Request : User ID or Message IDs are missing : {request.user_id}, {request.message_ids}")
        return GetMessagesStatusResponse(
            status="error",
            data=[]
        )

    object_ids = convert_string_ids_to_object_ids(request.message_ids)
    mongo = MongoQueryApplicator(CollectionNames.CHAT.value)
    messages = await mongo.find(
        {"_id": {"$in": object_ids}, "user_id": ObjectId(request.user_id)},
    )
    
    for message in messages:
        res.append(MessageStatus(
            message_id=str(message["_id"]),
            status=message["system_message_status"],
            system_response=message["system_message"]
        ))
    logger.info(f"Successfully fetched {len(res)} messages status for user {request.user_id}")

    return GetMessagesStatusResponse(
        status="success",
        data=res
    )
