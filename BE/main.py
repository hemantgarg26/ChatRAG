from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse
import time

from app.core.config import settings
from app.utils.logger import get_logger
from app.api.health import router as health_router
from app.api.neuro_chat_endpoints import router as neuro_chat_router
from app.utils.db_connect import mongodb
from app.core.pinecone_config import pinecone
from app.core.embeddings_config import embeddings

logger = get_logger("main")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="APIs for Neuro Chat",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

'''
    Adding middleware for Authorization, Authentication and Logging
'''
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0]
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # Log request
    logger.info(f"Request received: {request.method} {request.url.path} from {client_ip}")
    
    response = await call_next(request)
    
    # Calculate and log processing time
    process_time = time.time() - start_time
    logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    
    # Add processing time header to response
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include Routers
app.include_router(health_router, prefix="/api/health")
app.include_router(neuro_chat_router, prefix="/api/chat")

'''
    DB Setup
'''
@app.on_event("startup")
async def startup_event():
    await mongodb.connect()
    await pinecone.initialize_connection()
    await embeddings.initialize_embeddings()
    logger.info("Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_event():
    await mongodb.close()
    await pinecone.close()
    logger.info("Disconnected from MongoDB and Pinecone")

@app.get("/")
async def root():
    """
    Root endpoint.
    Returns:
        dict: Welcome message with API info
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION
    } 


# Serve Swagger UI using custom openapi.yaml
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="./openapi.yaml",
        title="Neuro Chat Docs"
    )

# Serve the YAML file
@app.get("/openapi.yaml", include_in_schema=False)
async def openapi_yaml():
    return FileResponse("openapi.yaml", media_type="application/yaml")