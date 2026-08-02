import asyncio
import uuid
from typing import BinaryIO

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageUploadError(Exception):
    """Raised when a file fails to upload to the object storage backend."""


class FilebaseStorageManager:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.FILEBASE_ACCESS_KEY,
            aws_secret_access_key=settings.FILEBASE_SECRET_KEY,
            endpoint_url=settings.FILEBASE_ENDPOINT,
            config=BotoConfig(signature_version="s3v4"),
        )
        self.bucket_name = settings.FILEBASE_BUCKET_NAME

    def _upload_sync(self, file_object: BinaryIO, key: str, content_type: str) -> None:
        """
        Synchronously uploads a file to the object storage backend.

        :param file_object: A file-like object to be uploaded
        :param key: The key under which the file should be stored
        :param content_type: The MIME type of the file
        :raises StorageUploadError: If the upload fails
        """

        try:
            self.s3_client.upload_fileobj(
                Fileobj=file_object,
                Bucket=self.bucket_name,
                Key=key,
                ExtraArgs={"ContentType": content_type},
            )
        except ClientError as e:
            raise StorageUploadError(f"Filebase upload failed for key '{key}': {e}") from e

    async def upload_document(self, file_object: BinaryIO, key: str, content_type: str) -> str:
        """Uploads a file and returns the storage key. Raises StorageUploadError on failure."""
        await asyncio.to_thread(self._upload_sync, file_object, key, content_type)
        return key

    def _presign_sync(self, key: str, expires_in: int) -> str:
        """
        Generates a presigned URL to fetch a file from the object storage backend.

        :param key: The key under which the file is stored
        :param expires_in: The number of seconds after which the presigned URL expires
        :return: A presigned URL
        """
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )

    async def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generates a presigned URL to fetch a file from the object storage backend.

        :param key: The key under which the file is stored
        :param expires_in: The number of seconds after which the presigned URL expires
        :return: A presigned URL
        :raises StorageUploadError: If the upload fails
        """
        return await asyncio.to_thread(self._presign_sync, key, expires_in)

    @staticmethod
    def build_student_doc_key(application_id: uuid.UUID, doc_type: str, filename: str) -> str:
        """
        Builds a storage key for a student application document.

        :param application_id: The application ID under which the document is associated
        :param doc_type: The type of document being uploaded (e.g. "income_certificate")
        :param filename: The original filename of the uploaded document
        :return: A storage key in the format "student-docs/{application_id}/{doc_type}/{uuid}_{filename}"
        """
        return f"student-docs/{application_id}/{doc_type}/{uuid.uuid4()}_{filename}"

    @staticmethod
    def build_admin_doc_key(application_id: uuid.UUID, doc_label: str, filename: str) -> str:
        """
        Builds a storage key for an admin application document.

        :param application_id: The application ID under which the document is associated
        :param doc_label: A label describing the type of document being uploaded (e.g. "income_certificate")
        :param filename: The original filename of the uploaded document
        :return: A storage key in the format "admin-docs/{application_id}/{doc_label}/{uuid}_{filename}"
        """
        return f"admin-docs/{application_id}/{doc_label}/{uuid.uuid4()}_{filename}"


storage_manager = FilebaseStorageManager()