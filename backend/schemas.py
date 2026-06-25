from typing import Optional
from pydantic import BaseModel


class QuestionRequest(
    BaseModel
):
    question: str


class UploadRequest(
    BaseModel
):
    subject: Optional[str] = None
    topic: Optional[str] = None


class HealthResponse(
    BaseModel
):
    status: str


class AskResponse(
    BaseModel
):
    task_id: Optional[str] = None
    answer: Optional[str] = None


class UploadResponse(
    BaseModel
):
    document_id: str
    parent_id: str
    file_name: str
    subject: str
    topic: str
    status: str


class DocumentOverviewResponse(BaseModel):
    document_id: str
    parent_id: str
    filename: str
    subject: str
    topic: str
    total_pages: int
    total_chunks: int
    status: str


class CompareRequest(
    BaseModel
):
    question: str
    answer: str


class VoiceResponse(
    BaseModel
):
    task_id: Optional[str] = None
    transcript: str
    language: str
    answer: Optional[str] = None


class UpdateQARequest(
    BaseModel
):
    question: str
    answer: str


class CreateQARequest(
    BaseModel
):
    question: str
    answer: str


class QAResponse(BaseModel):
    id: int
    question: str
    answer: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    document_id: Optional[str] = None
    verified: bool
