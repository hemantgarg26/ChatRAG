from app.core.config import settings 

import os
import json
from typing import Optional, List, Dict, Any, Union
from pinecone import Pinecone, ServerlessSpec

class PineconeManager:
    """
    Pinecone connection manager for the application.
    Handles index management and lifecycle.
    """
    
    def __init__(self):
        self.pinecone_client: Optional[Pinecone] = None
        self.index_name: str = settings.PINECONE_INDEX_NAME
        self.index = None
        self.dimension: int = 1536  # For text-embedding-3-small
    
    async def initialize_connection(
        self, 
        api_key: Optional[str] = None,
        index_name: str = settings.PINECONE_INDEX_NAME,
        dimension: int = 1536,
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1"
    ) -> None:
        """
        Initialize Pinecone connection and create/connect to index.
        
        Args:
            api_key: Pinecone API key (if None, uses PINECONE_API_KEY env var)
            index_name: Name of the Pinecone index
            dimension: Dimension of the embeddings
            metric: Distance metric for the index
            cloud: Cloud provider for serverless
            region: Region for serverless deployment
        """
        try:
            # Initialize Pinecone client
            api_key = api_key or os.getenv("PINECONE_API_KEY")
            if not api_key:
                raise ValueError("Pinecone API key not provided. Set PINECONE_API_KEY environment variable.")
            
            self.pinecone_client = Pinecone(api_key=api_key)
            self.index_name = index_name
            self.dimension = dimension
            
            # Check if index exists, create if not
            existing_indexes = self.pinecone_client.list_indexes()
            index_names = [index.name for index in existing_indexes]
            
            if index_name not in index_names:
                print(f"Creating new Pinecone index: {index_name}")
                self.pinecone_client.create_index(
                    name=index_name,
                    dimension=dimension,
                    metric=metric,
                    spec=ServerlessSpec(
                        cloud=cloud,
                        region=region
                    )
                )
            else:
                print(f"Using existing Pinecone index: {index_name}")
            
            # Connect to the index
            self.index = self.pinecone_client.Index(index_name)
            
            # Test the connection
            stats = self.index.describe_index_stats()
            print(f"Successfully connected to Pinecone index '{index_name}' with {stats['total_vector_count']} vectors")
            
        except Exception as e:
            raise Exception(f"Error initializing Pinecone connection: {str(e)}")
    
    async def get_index(self):
        """
        Get the Pinecone index instance.
        
        Returns:
            Pinecone index instance
            
        Raises:
            RuntimeError: If Pinecone connection is not initialized
        """
        if self.index is None:
            raise RuntimeError("Pinecone connection not initialized. Call initialize_connection() first.")
        return self.index
    
    
    async def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        """
        Upsert vectors to the Pinecone index.
        Args:
            vectors: List of vector dictionaries with id, values, and metadata
        """
        if self.index is None:
            raise RuntimeError("Pinecone connection not initialized.")
        
        # Process vectors to ensure metadata compatibility
        processed_vectors = []
        for vector in vectors:
            processed_vector = {
                "id": vector["id"],
                "values": vector["values"]
            }
            
            processed_vectors.append(processed_vector)
        
        self.index.upsert(vectors=processed_vectors)  # type: ignore
    
    async def query_vectors(self, vector: List[float], top_k: int = 5, 
                     filter_dict: Optional[Dict[str, Any]] = None,
                     include_metadata: bool = True) -> Any:
        """
        Query vectors from the Pinecone index.
        
        Args:
            vector: Query vector
            top_k: Number of top results to return
            filter_dict: Optional filter dictionary
            include_metadata: Whether to include metadata in results
            
        Returns:
            Query results from Pinecone
        """
        if self.index is None:
            raise RuntimeError("Pinecone connection not initialized.")
        
        return self.index.query(
            vector=vector,
            top_k=top_k,
            filter=filter_dict,
            include_metadata=include_metadata
        )
    
pinecone = PineconeManager()