# app/ai/workflows/document_validation_workflow.py

import json
import uuid
from typing import Optional

from workflows import Workflow, step
from workflows.events import Event, StartEvent, StopEvent
from llama_index.core.workflow import Context, InputRequiredEvent, HumanResponseEvent
from llama_index.readers.s3 import S3Reader

from app.ai.validation.cross_match import cross_match_documents
from app.core.config import settings
from app.ai.schemas.doc_validation_schemas import Marksheet
from app.ai.schemas.doc_validation_schemas import GovernmentIDCard

from app.models.enums import DocumentType


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------

class DocumentsLoadedEvent(Event):
    application_id: uuid.UUID
    documents: list  # list of llama_index Document objects, each tagged with doc_type


class DocExtractionRequestEvent(Event):
    application_id: uuid.UUID
    doc_type: str
    text: str


class DocExtractedEvent(Event):
    doc_type: str
    extracted: dict  # parsed JSON fields from the structured LLM call


class AllExtractedEvent(Event):
    application_id: uuid.UUID
    extracted_docs: list  # list[DocExtractedEvent]


class ValidationScoredEvent(Event):
    application_id: uuid.UUID
    flags: int
    issues: str
    extracted_docs: list


# --------------------------------------------------------------------------
# Workflow
# --------------------------------------------------------------------------

class DocumentValidationWorkflow(Workflow):
    """
    Loads a student's uploaded documents, extracts structured fields from
    each via Gemini, cross-checks them against each other and against the
    student's registration/application record, and routes the result:
      - flags == 0            -> auto-approved
      - 0 < flags < threshold -> sent to an admin for manual review (HITL)
      - flags >= threshold    -> auto-rejected
    """

    def __init__(
        self,
        document_service,
        application_repository,
        llm,
        threshold: int = 3,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.document_service = document_service
        self.application_repository = application_repository
        self.llm = llm
        self.threshold = threshold

        # doc_type -> pydantic schema used for structured extraction
        self.schema_map = {
            DocumentType.CLASS12_MARKSHEET.value: Marksheet,
            DocumentType.ID_CARD.value: GovernmentIDCard,
        }


    # ----------------------------------------------------------------
    # Step 1: Load all documents for the application from S3
    # ----------------------------------------------------------------
    @step
    async def load_documents(self, ev: StartEvent) -> DocumentsLoadedEvent:
        application_id: uuid.UUID = ev.application_id

        application_documents = await self.document_service.list_application_documents(
            application_id
        )

        documents = []
        for doc in application_documents:
            # Only CLASS12_MARKSHEET / ID_CARD go through the AI workflow.
            # INCOME_CERTIFICATE / OTHER are validated manually via
            # PATCH /documents/{document_id}/verify instead.
            if doc.doc_type not in self.schema_map:
                continue

            reader = S3Reader(
                bucket=settings.FILEBASE_BUCKET_NAME,
                key=doc.storage_key,
                aws_access_id=settings.FILEBASE_ACCESS_KEY,
                aws_access_secret=settings.FILEBASE_SECRET_KEY,
                s3_endpoint_url=settings.FILEBASE_ENDPOINT,
            )
            loaded = reader.load_data()
            for d in loaded:
                print(f"--- RAW TEXT [{doc.doc_type}] ---")
                print(repr(d.text[:1000]))
                d.metadata["doc_type"] = doc.doc_type
            documents.extend(loaded)

        return DocumentsLoadedEvent(application_id=application_id, documents=documents)

    # ----------------------------------------------------------------
    # Step 2: Dispatch one extraction request per document (parallel fan-out)
    # ----------------------------------------------------------------
    @step
    async def dispatch_extractions(
        self, ctx: Context, ev: DocumentsLoadedEvent
    ) -> Optional[DocExtractionRequestEvent]:
        await ctx.store.set("application_id", ev.application_id)
        await ctx.store.set("expected_count", len(ev.documents))

        for doc in ev.documents:
            ctx.send_event(
                DocExtractionRequestEvent(
                    application_id=ev.application_id,
                    doc_type=doc.metadata["doc_type"],
                    text=doc.text,
                )
            )
        return None

    # ----------------------------------------------------------------
    # Step 3: Run structured extraction for a single document
    # ----------------------------------------------------------------
    @step(num_workers=4)
    async def extract_single_document(
        self, ev: DocExtractionRequestEvent
    ) -> DocExtractedEvent:
        schema = self.schema_map.get(ev.doc_type)
        if schema is None:
            return DocExtractedEvent(doc_type=ev.doc_type, extracted={})

        sllm = self.llm.as_structured_llm(schema)
        response = await sllm.acomplete(ev.text)
        extracted = json.loads(response.text)

        return DocExtractedEvent(doc_type=ev.doc_type, extracted=extracted)

    # ----------------------------------------------------------------
    # Step 4: Collect all extraction results before continuing
    # ----------------------------------------------------------------
    @step
    async def collect_extractions(
        self, ctx: Context, ev: DocExtractedEvent
    ) -> Optional[AllExtractedEvent]:
        expected_count = await ctx.store.get("expected_count")
        application_id = await ctx.store.get("application_id")

        results = ctx.collect_events(ev, [DocExtractedEvent] * expected_count)
        if results is None:
            return None  # still waiting on other extractions

        return AllExtractedEvent(application_id=application_id, extracted_docs=results)

    # ----------------------------------------------------------------
    # Step 5: Cross-match extracted fields, compute flags + issues
    # ----------------------------------------------------------------
    @step
    async def match_and_score(self, ev: AllExtractedEvent) -> ValidationScoredEvent:
        by_type = {d.doc_type: d.extracted for d in ev.extracted_docs}
        marksheet = by_type.get(DocumentType.CLASS12_MARKSHEET.value, {})
        id_card = by_type.get(DocumentType.ID_CARD.value, {})

        # ASSUMPTION: application_repository.get_by_id() eager-loads (or lazy
        # loads, if your session/relationship setup allows it in an async
        # context) the related Student via Application.student.
        application = await self.application_repository.get_with_student(ev.application_id)
        student = application.student

        #for debugging
        print("MARKSHEET:", marksheet)
        print("ID CARD:", id_card)
        print("REG NAME:", student.name if student else None)
        print("REG DOB:", student.date_of_birth if student else None)

        result = cross_match_documents(
            marksheet=marksheet,
            id_card=id_card,
            registration_name=student.name if student else None,
            registration_dob=student.date_of_birth if student else None,
        )

        return ValidationScoredEvent(
            application_id=ev.application_id,
            flags=result.flags,
            issues=result.issues_string,
            extracted_docs=ev.extracted_docs,
        )

    # ----------------------------------------------------------------
    # Step 6: Route based on flag count — auto-approve, admin review, or reject
    # ----------------------------------------------------------------


    @step
    async def route_decision(
        self, ctx: Context, ev: ValidationScoredEvent
    ) -> StopEvent:
        processed_doc_types = [d.doc_type for d in ev.extracted_docs]

        if ev.flags == 0:
            await self.document_service.mark_validated(ev.application_id, processed_doc_types)
            return StopEvent(result={"status": "validated", "flags": 0, "issues": ""})

        if ev.flags >= self.threshold:
            await self.document_service.mark_rejected(
                ev.application_id, reason=ev.issues, doc_types=processed_doc_types
            )
            return StopEvent(
                result={"status": "rejected", "flags": ev.flags, "issues": ev.issues}
            )

        await self.document_service.mark_pending_review(
            ev.application_id, flags=ev.flags, issues=ev.issues, doc_types=processed_doc_types
        )
        return StopEvent(
            result={"status": "pending_review", "flags": ev.flags, "issues": ev.issues}
        )


    


