# test_s3_reader.py — run standalone, no LLM involved
from llama_index.readers.s3 import S3Reader
from app.core.config import settings

reader = S3Reader(
    bucket=settings.FILEBASE_BUCKET_NAME,
    key="student-docs/f874a69a-bcbf-4f14-a6f0-c707885a4c0c/CLASS12_MARKSHEET/06841ad5-6bca-4af2-afee-2cfdf750a30b_RIJU-BOSE-MARKSHEET.pdf",  # copy from the documents table
    aws_access_id=settings.FILEBASE_ACCESS_KEY,
    aws_access_secret=settings.FILEBASE_SECRET_KEY,
    s3_endpoint_url=settings.FILEBASE_ENDPOINT,
)
docs = reader.load_data()
for d in docs:
    print(repr(d.text[:1000]))