from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from fastapi import UploadFile
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

class DocumentIn(BaseModel):
    title: str
    content: str

class DocumentOut(BaseModel):
    id: str
    title: str
    created_at: Optional[datetime]
    uploader: Optional[UserOut]
    model_config = ConfigDict(from_attributes=True)
    # class Config:
    #     orm_mode = True

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[DocumentOut]

class User(BaseModel):
    username: str
    password: str

class FileUploadResponse(BaseModel):
    filenames: list[str]
    status: str 