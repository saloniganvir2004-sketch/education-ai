from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    question: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    source: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    confidence: Optional[float] = None

class ChatContext(BaseModel):
    subject: Optional[str] = None
    topic: Optional[str] = None

class ChatMetadata(BaseModel):
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatRequestV2(BaseModel):
    question: str
    context: Optional[ChatContext] = None
    metadata: Optional[ChatMetadata] = None

class ChatSource(BaseModel):
    subject: Optional[str] = None
    topic: Optional[str] = None
    document_id: Optional[str] = None

class ChatResponseV2(BaseModel):
    answer: str
    source: Optional[str] = None
    confidence: Optional[float] = None
    context: Optional[ChatContext] = None
    metadata: Optional[ChatMetadata] = None
    retrieval_source: Optional[ChatSource] = None