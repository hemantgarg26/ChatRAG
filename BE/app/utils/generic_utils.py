from typing import List
from bson import ObjectId
from app.utils.logger import get_logger

logger = get_logger("generic_utils")


def convert_string_ids_to_object_ids(ids: List[str]) -> List[ObjectId]:
    object_ids = []
    for msg_id in ids:
        try:
            object_ids.append(ObjectId(msg_id))
        except Exception as e:
            logger.warning(f"Invalid ObjectId format: {msg_id}, skipping")
            continue
    return object_ids