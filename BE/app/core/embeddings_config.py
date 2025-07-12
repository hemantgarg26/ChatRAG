from langchain_community.embeddings import HuggingFaceBgeEmbeddings

class EmbeddingsConfig:
    def __init__(self):
        self.model_name = "BAAI/bge-small-en-v1.5"
        self.model_kwargs = {"device": "cpu"}
        self.encode_kwargs = {"normalize_embeddings": True}
        self.hf = None
        self.initialized = False

    async def initialize_embeddings(self):
        # Check if already initialized
        if self.is_initialized():
            print(f"Embeddings config already initialized with model '{self.model_name}'")
            return self.hf
            
        print(f"Initializing embeddings with model '{self.model_name}'")
        self.hf = HuggingFaceBgeEmbeddings(
            model_name=self.model_name, 
            model_kwargs=self.model_kwargs, 
            encode_kwargs=self.encode_kwargs
        )
        self.initialized = True
        return self.hf

    def is_initialized(self) -> bool:
        """
        Check if embeddings are initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self.initialized and self.hf is not None

embeddings = EmbeddingsConfig()