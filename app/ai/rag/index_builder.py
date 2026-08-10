from app.ai.config import get_vector_store_instance
from llama_index.readers.s3 import S3Reader
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter


from app.ai.config import get_embedding_model
from app.ai.rag.corpora import CorpusConfig
from app.core.config import settings



def build_index(corpus: CorpusConfig) -> None:
    # step 1: configure embed model
    embed_model = get_embedding_model()
    
    # step 2: configure s3 reader
    reader = S3Reader(
        bucket = settings.FILEBASE_BUCKET_NAME,
        key = corpus.storage_key,
        aws_access_id=settings.FILEBASE_ACCESS_KEY,
        aws_access_secret=settings.FILEBASE_SECRET_KEY,
        s3_endpoint_url=settings.FILEBASE_ENDPOINT,
    )
    
    # step 3: read the document
    document = reader.load_data()
    
    if not document:
        raise RuntimeError(f"No document found at key '{corpus.storage_key}'")
        
    # step 4: configure splitter
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)
    nodes = splitter.get_nodes_from_documents(document)
    
    # step 5: configure vector store
    vector_store = get_vector_store_instance(corpus.table_name)
    
    # step 6: configure storage context
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # step 7: configure vector store index
    VectorStoreIndex(
        nodes=nodes,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True,
    )
    
   
