from api import client


def upload_document(
    doc_type: str, filename: str, file_bytes: bytes, content_type: str
) -> dict:
    """
    doc_type must be one of DOCUMENT_TYPES (see utils/constants.py).
    content_type must be an AllowedFileType value (PDF or DOCX mime type).
    """
    files = {"file": (filename, file_bytes, content_type)}
    data = {"doc_type": doc_type}
    return client.post("/documents/upload", data=data, files=files)


def request_validation(application_id: str) -> dict:
    return client.post(f"/documents/applications/{application_id}/documents/validate")


def list_my_documents() -> list[dict]:
    return client.get("/documents/me")