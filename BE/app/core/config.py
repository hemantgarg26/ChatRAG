from dotenv import load_dotenv, get_key
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    """Application settings."""
    APP_NAME: str = "Neuro Chat is online"
    APP_VERSION: str = "0.1.0"
    MONGO_URI: str = get_key(".env", "MONGO_URI")
    MONGO_DB:str = get_key(".env", "MONGO_DB")
    MESSAGES_PER_PAGE: int = 10

    # Celery
    BROKER_URL : str = get_key(".env", "BROKER_URL")
    BACKEND_URL : str = get_key(".env", "BACKEND_URL") 

    #PINECONE
    PINECONE_API_KEY: str = get_key(".env", "PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = get_key(".env", "PINECONE_INDEX_NAME")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a settings object
settings = Settings() 