# app/ai/config.py
from urllib.parse import urlparse
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import Settings
from llama_index.vector_stores.postgres import PGVectorStore
# embedding model
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# Import your single source of truth configurations directly
from app.core.config import settings

def initialize_ai_environment() -> GoogleGenAI:
    """
    Initializes the central Google GenAI model instance using validated 
    Pydantic settings and registers it globally within LlamaIndex.
    """
    # Instantiate the LlamaIndex LLM client directly from your Pydantic settings
    llm = GoogleGenAI(
        model=settings.GEMINI_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
    # Instantiate the embed_model
    embed_model = GoogleGenAIEmbedding(
    model_name="text-embedding-004",
    api_key=settings.GOOGLE_API_KEY,
    )

    # Assign globally so all sub-agents inherit this framework engine by default
    Settings.llm = llm
    Settings.embed_model = embed_model
    
    return llm


def get_embedding_model() -> GoogleGenAIEmbedding:
    embed_model = GoogleGenAIEmbedding(
    model_name="text-embedding-004",
    api_key=settings.GOOGLE_API_KEY,
    )

    return embed_model

async def get_vector_store_instance() -> PGVectorStore:
    """
    Establishes an asynchronous vector database storage engine connection interface 
    by parsing your validated Pydantic DATABASE_URL string.
    """
    # Clean out the internal python +asyncpg connector prefix for raw driver compatibility
    clean_postgres_url = settings.DATABASE_URL.replace("+asyncpg", "")
    
    # Parse out connection details cleanly

    parsed = urlparse(clean_postgres_url)
    username = parsed.username
    password = parsed.password or ""
    host = parsed.hostname
    port = parsed.port or 5432
    db_name = parsed.path.lstrip("/")

    # Return the persistent vector engine table mapper interface
    return PGVectorStore.from_params(
        host=host,
        port=port,
        database=db_name,
        user=username,
        password=password,
        table_name="vector_knowledge_embeddings",
        embed_dim=768  # 768 dimensions match Google's text-embedding-004 model standard
    )
