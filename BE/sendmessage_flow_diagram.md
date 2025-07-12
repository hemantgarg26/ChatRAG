# SendMessage API Flow Diagram

```mermaid
flowchart TD
    A[Client - React Frontend] -->|"1. User Types Message"| B[Chat Component]
    B -->|"2. POST /api/chat/sendMessage<br/>{user_id, message}"| C[FastAPI - sendMessage Endpoint]
    
    C -->|"3. Validate User"| D[MongoDB - Users Collection]
    D -->|"User Found"| E[MongoDB - Chat Collection]
    C -->|"4. Save Message<br/>(status: PROCESSING)"| E
    E -->|"5. Return message_id"| F[CeleryTaskQueue.process_message]
    
    F -->|"6. Send Task to Queue"| G[Redis Broker]
    G -->|"7. Task Queued"| H[Celery Worker]
    
    H -->|"8. process_message_task.delay(message_id)"| I[Celery Worker Service]
    I -->|"9. Validate Message ID"| E
    I -->|"10. Extract user_message"| J[Embeddings Service<br/>BAAI/bge-small-en-v1.5]
    J -->|"11. Generate Vector<br/>Embeddings"| K[Pinecone Vector DB]
    
    K -->|"12. Query Similar Vectors<br/>(top_k=5)"| L[Related Message IDs]
    L -->|"13. Fetch Related Messages"| E
    E -->|"14. System Messages Context"| M[LLM Service - GPT-2]
    
    M -->|"15. Generate Response<br/>with Context"| N[System Response]
    N -->|"16. Update Message<br/>(status: SUCCESS)"| E
    N -->|"17. Upsert New Vector"| K
    
    subgraph "Frontend Polling"
        O[Frontend Timer] -->|"18. Poll Status<br/>POST /api/chat/getMessagesStatus"| P[FastAPI - getMessagesStatus]
        P -->|"19. Check Status"| E
        E -->|"20. Return Status & Response"| P
        P -->|"21. Status Response"| Q[Update Chat UI]
    end
    
    C -->|"Immediate Response<br/>message_id, status: processing"| R[Frontend Receives Response]
    R -->|"22. Start Polling"| O
    
    subgraph "Backend Services"
        direction TB
        S[FastAPI Main App<br/>Port 8000]
        T[Celery Worker Process]
        U[Redis Broker<br/>Port 6379]
        V[MongoDB Database]
        W[Pinecone Vector Store]
        X[LLM - GPT-2 Model]
        Y[Embeddings Model]
    end
    
    subgraph "Error Handling"
        Z[Processing Error] -->|"Update Status: ERROR"| E
        AA[Timeout] -->|"Frontend Timeout"| Q
    end
    
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef api fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef queue fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef database fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef ml fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class A,B,O,Q,R frontend
    class C,P,S api
    class F,G,H,I,T,U queue
    class D,E,V database
    class J,K,L,M,N,W,X,Y ml
```

## Flow Description

### 1. User Interaction (Frontend)
- User types message in React chat component
- Frontend calls `POST /api/chat/sendMessage` with user_id and message

### 2. API Processing (FastAPI)
- **Endpoint**: `/api/chat/sendMessage`
- **Validation**: Check if user exists in Users collection
- **Storage**: Save message to Chat collection with status "PROCESSING"
- **Queue**: Send task to Celery via Redis broker
- **Response**: Return message_id and processing status immediately

### 3. Background Processing (Celery Worker)
- **Task**: `process_message_task.delay(message_id)`
- **Validation**: Verify message exists in database
- **Embeddings**: Generate vector using BAAI/bge-small-en-v1.5 model
- **Similarity Search**: Query Pinecone for top 5 similar vectors
- **Context Retrieval**: Fetch related messages from MongoDB
- **LLM Generation**: Generate response using GPT-2 with context
- **Update**: Save response to database and update status
- **Vector Storage**: Store new vector in Pinecone for future similarity searches

### 4. Status Polling (Frontend)
- **Polling**: Frontend polls `POST /api/chat/getMessagesStatus` every 10 seconds
- **Status Check**: Backend checks message status in database
- **UI Update**: Frontend updates chat interface when response is ready

### 5. Error Handling
- **Processing Errors**: Update message status to ERROR in database
- **Timeout**: Frontend stops polling after maximum retries
- **Graceful Degradation**: System continues to work even if some components fail

## Key Components

- **Frontend**: React.js with axios for API calls
- **API**: FastAPI with async/await support
- **Queue**: Redis as message broker
- **Worker**: Celery for background task processing
- **Database**: MongoDB for persistent storage
- **Vector DB**: Pinecone for similarity search
- **ML Models**: GPT-2 for response generation, BGE embeddings for vectors 