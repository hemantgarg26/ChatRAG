from app.dtos.collection_names import CollectionNames
from app.dtos.error_success_codes import ErrorAndSuccessCodes
from app.utils.db_query import MongoQueryApplicator
from app.utils.logger import get_logger
from app.core.embeddings_config import embeddings
from app.core.pinecone_config import pinecone
from app.core.llm import get_llm_response

from bson import ObjectId
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

logger = get_logger("celery_worker_service")


async def validate_message_id(message_id: str) -> Optional[Dict[str, Any]]:
    """
    Validate if the message_id exists in the chats collection.
    Args:
        message_id: The _id of the message to validate
    Returns:
        Optional[Dict]: The message document if found, None otherwise
    """
    try:
        mongo = MongoQueryApplicator(CollectionNames.CHAT.value)
        message_doc = await mongo.find_one({"_id": ObjectId(message_id)})
        
        if not message_doc:
            logger.warning(f"Message not found with ID: {message_id}")
            return None
            
        logger.info(f"Message validated successfully: {message_id}")
        return message_doc
        
    except Exception as e:
        logger.error(f"Error validating message ID {message_id}: {str(e)}")
        return None
    
async def get_related_messages(related_message_ids: List[str]):
    related_messages = []

    if not related_message_ids:
        logger.error("No related message IDs found")
        return related_messages
    
    mongo = MongoQueryApplicator(CollectionNames.CHAT.value)
    # Convert string IDs to ObjectIds for MongoDB query
    object_ids = []
    for msg_id in related_message_ids:
        try:
            object_ids.append(ObjectId(msg_id))
        except Exception as e:
            logger.warning(f"Invalid ObjectId format: {msg_id}, skipping")
            continue
    
    if object_ids:
        # Query messages with the ObjectIds
        related_messages = await mongo.find(
            {"_id": {"$in": object_ids}},
            limit=5
        )
    
    if len(related_messages) == 0:
        logger.error("No related messages found")
        return related_messages

    system_messages = []
    for msg in related_messages:
        if msg.get("system_message"):
            system_messages.append({
                "user" : msg.get("user_message", ""),
                "system" : msg.get("system_message", "")
            })
    return system_messages


async def process_message_inside_task_queue(message_id: str):
    """
    Process message inside Celery task queue.
    
    Steps:
    1. Validate message_id exists in chats collection
    2. Convert user message to vector embeddings
    3. Query Pinecone for top 5 similar vectors
    4. Extract message IDs from Pinecone results
    5. Fetch related messages from chats collection
    6. Create system response from related messages
    7. Update original message with system response
    
    Args:
        message_id: The _id of the message in chats collection
        
    Returns:
        str: Status message
    """
    try:
        # Step 1: Validate message_id exists in chats collection
        message_doc = await validate_message_id(message_id)
        if not message_doc:
            logger.error(f"Invalid message ID: {message_id}")
            return "Invalid message ID"
        
        user_message = message_doc.get("user_message", "")
        if not user_message:
            logger.error(f"No user message found for ID: {message_id}")
            return "No user message found"
        
        logger.info(f"Processing message: {user_message[:50]}...")
        
        # Step 2: Convert user message to vector embeddings
        embeddings_model = await embeddings.initialize_embeddings()
        message_vector = embeddings_model.embed_query(user_message)
        
        logger.info(f"Generated embeddings for message: {message_id}")
        
        # Step 3: Query Pinecone for top 5 similar vectors
        query_response = await pinecone.query_vectors(
            vector=message_vector,
            top_k=5,
            include_metadata=True
        )
        
        logger.info(f"Pinecone query returned {len(query_response.matches)} matches")
        
        # Step 4: Extract message IDs from Pinecone results
        related_message_ids = []
        for match in query_response.matches:
            # The _id field in Pinecone should contain the MongoDB _id of chat messages
            pinecone_id = match.id
            related_message_ids.append(pinecone_id)
        
        logger.info(f"Found {len(related_message_ids)} related message IDs")
        logger.info(f"Message Ids {related_message_ids} related message IDs")
        
        # Step 5: Fetch related messages from chats collection
        system_messages = await get_related_messages(related_message_ids);
        
        # Step 6: Send to LLM Model to get system response
        # Generate response using GPT-2 with context
        system_response = await get_llm_response(user_message, system_messages)
        logger.info(f"LLM generated response for message {message_id}, Response: {system_response}")
        
        # Step 7: Update original message with system response
        mongo = MongoQueryApplicator(CollectionNames.CHAT.value)
        update_result = await mongo.update_one(
            {"_id": ObjectId(message_id)},
            {
                "system_message": system_response,
                "system_message_status": ErrorAndSuccessCodes.MESSAGE_PROCESSING_SUCCESS.value,
                "updated_at": datetime.now()
            }
        )
        
        logger.info(f"Successfully updated message {message_id} with system response")
        
        # Step 8: Upsert vector to Pinecone with the complete conversation
        try:
            vector_data = [{
                "id": message_id,
                "values": message_vector
            }]
            
            await pinecone.upsert_vectors(vector_data)
            logger.info(f"Successfully upserted vector to Pinecone for message {message_id}")
            
        except Exception as pinecone_error:
            logger.error(f"Error upserting vector to Pinecone for message {message_id}: {str(pinecone_error)}")
            # Don't fail the entire process if Pinecone upsert fails
        
        return "Message processed successfully"
    except Exception as e:
        logger.error(f"Error processing message {message_id}: {str(e)}")
        
        # Update message status to failed
        try:
            mongo = MongoQueryApplicator(CollectionNames.CHAT.value)
            await mongo.update_one(
                {"_id": ObjectId(message_id)},
                {
                    "system_message": "Sorry, I encountered an error processing your message. Please try again.",
                    "system_message_status": ErrorAndSuccessCodes.PROCESSING_ERROR.value,
                    "updated_at": datetime.now()
                }
            )
        except Exception as update_error:
            logger.error(f"Failed to update error status for message {message_id}: {str(update_error)}")
        
        return "Error processing message"