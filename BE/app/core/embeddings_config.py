from langchain_community.embeddings import HuggingFaceBgeEmbeddings

class EmbeddingsConfig:
    def __init__(self):
        self.model_name = "TaylorAI/bge-micro"
        self.model_kwargs = {"device": "cpu"}
        self.encode_kwargs = {"normalize_embeddings": True}
        self.hf = HuggingFaceBgeEmbeddings(model_name=self.model_name, model_kwargs=self.model_kwargs, encode_kwargs=self.encode_kwargs)

    async def initialize_embeddings(self):
        return self.hf

embeddings = EmbeddingsConfig()