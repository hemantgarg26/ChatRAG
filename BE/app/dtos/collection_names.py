from enum import Enum

class CollectionNames(Enum):
    USERS = "users"
    CHAT = "chats"

class ChatOwners(Enum):
    USER = "user"
    SYSTEM = "system"