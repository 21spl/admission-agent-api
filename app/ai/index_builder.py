from app.ai.config import get_embedding_model
from app.ai.config import get_vector_store_instance
from app.ai.config import initialize_ai_environment
from app.core.config import settings

from llama_index.readers.s3 import S3Reader



embed_dim = 768

def build_doc_index() -> None:

    # step 1: define the embedding model
    embed_model = get_embedding_model()

    # step 2: configure s3 reader
    reader = S3Reader(
                    bucket=settings.FILEBASE_BUCKET_NAME,
                    key=doc.storage_key,
                    aws_access_id=settings.FILEBASE_ACCESS_KEY,
                    aws_access_secret=settings.FILEBASE_SECRET_KEY,
                    s3_endpoint_url=settings.FILEBASE_ENDPOINT,
                )

