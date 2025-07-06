from fastapi import FastAPI, Depends, HTTPException, status, Body, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from .schemas import DocumentIn, DocumentOut, QueryRequest, QueryResponse, UserCreate, UserOut
from .auth import get_db, get_current_user, create_access_token, authenticate_user, get_password_hash
from .vector_store import lang_obj
from .llm import generate_answer_langchain, stream_answer_langchain
from .utils import chunk_text, extract_text_from_file
import uuid
from fastapi.staticfiles import StaticFiles
import os
import shutil
from .db import User, Document
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory='static'), name="static")
UPLOAD_DIR = "./app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Hardcoded user for demo
fake_user = {
    "username": "testuser",
    "hashed_password": get_password_hash("testpass")
}

@app.get("/")
def read_root():
    """
    Root endpoint for health check or welcome message.
    Returns:
        dict: A message indicating the API is running.
    """
    return {"message": "Document QA API is running."}

@app.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    Args:
        user (UserCreate): The user registration data (username, password).
        db (Session): SQLAlchemy database session (injected).
    Returns:
        UserOut: The registered user (id, username).
    Raises:
        HTTPException: If the username is already registered.
    """
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserOut(id=db_user.id, username=db_user.username)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT access token.
    Args:
        form_data (OAuth2PasswordRequestForm): The login form data (username, password).
        db (Session): SQLAlchemy database session (injected).
    Returns:
        dict: The access token and token type.
    Raises:
        HTTPException: If authentication fails.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/documents", response_model=list[DocumentOut])
async def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    List all documents uploaded by the current user.
    Args:
        user (User): The current authenticated user (injected).
        db (Session): SQLAlchemy database session (injected).
    Returns:
        list[DocumentOut]: List of documents (id, title, etc.) for the user.
    """
    docs = db.query(Document).filter(Document.uploader_id == user.id).all()
    return docs

@app.delete("/documents/{doc_id}")
async def delete_doc(doc_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Delete a document and its associated vectors for the current user.
    Args:
        doc_id (str): The document ID to delete.
        user (User): The current authenticated user (injected).
        db (Session): SQLAlchemy database session (injected).
    Returns:
        dict: Status of the deletion.
    Raises:
        HTTPException: If the document is not found or not owned by the user.
    """
    db_doc = db.query(Document).filter(Document.id == doc_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if db_doc.uploader_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this document")
    lang_obj.delete_document(doc_id, user.id)
    db.delete(db_doc)
    db.commit()
    return {"status": "deleted"}

@app.post("/query", response_model=QueryResponse)
async def query_qa(req: QueryRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Answer a question using vector search and LLM.
    Args:
        req (QueryRequest): The question to answer.
        user (User): The current authenticated user (injected).
        db (Session): SQLAlchemy database session (injected).
    Returns:
        QueryResponse: The generated answer and the source documents used.
    """
    results = lang_obj.search(req.question, user.id)
    doc_ids = set(r["doc_id"] for r in results)
    db_docs = {d.id: d for d in db.query(Document).filter(Document.id.in_(doc_ids)).all()}
    sources = [DocumentOut.model_validate(db_docs.get(r["doc_id"])) for r in results if r["doc_id"] in db_docs]
    # Deduplicate sources by document ID
    unique_sources = []
    seen_ids = set()
    for doc in sources:
        if doc.id not in seen_ids:
            unique_sources.append(doc)
            seen_ids.add(doc.id)
    context = "\n".join([r["content"] for r in results])
    answer = generate_answer_langchain(req.question, context)
    return QueryResponse(answer=answer, sources=unique_sources)

@app.post("/query/stream")
async def query_qa_stream(req: QueryRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Stream an LLM-generated answer to a question using vector search.
    Args:
        req (QueryRequest): The question to answer.
        user (User): The current authenticated user (injected).
        db (Session): SQLAlchemy database session (injected).
    Returns:
        StreamingResponse: The answer streamed token by token as plain text.
    """
    results = lang_obj.search(req.question, user.id)
    doc_ids = set(r["doc_id"] for r in results)
    db_docs = {d.id: d for d in db.query(Document).filter(Document.id.in_(doc_ids)).all()}
    context = "\n".join([r["content"] for r in results])
    async def streamer():
        async for token in stream_answer_langchain(req.question, context):
            yield token
    return StreamingResponse(streamer(), media_type="text/plain")

@app.post("/documents", response_model=list[DocumentOut])
async def add_documents(files: list[UploadFile] = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Upload and index documents for the current user.
    Accepts a list of files, extracts text, chunks, embeds, and indexes them in the vector store.
    Each chunk is embedded and saved with metadata (doc ID, title, user_id).
    Args:
        files (list[UploadFile]): The files to upload and index.
        user (User): The current authenticated user (injected).
        db (Session): SQLAlchemy database session (injected).
    Returns:
        list[DocumentOut]: The indexed documents for the user.
    Raises:
        HTTPException: If upload or processing fails.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    docs = []
    try:
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            try:
                text = extract_text_from_file(file_path)
            except Exception as e:
                os.remove(file_path)
                continue
            doc_id = str(uuid.uuid4())
            chunks = chunk_text(text)
            chunk_dicts = [{
                "doc_id": doc_id,
                "title": file.filename,
                "content": chunk
            } for chunk in chunks]
            lang_obj.add_document_chunks(chunk_dicts, user.id)

            db_doc = Document(id=doc_id, title=file.filename, content=text[:2000], uploader_id=user.id)
            db.add(db_doc)
            db.commit()
            db.refresh(db_doc)
            docs.append(db_doc)
            os.remove(file_path)
        return [DocumentOut.model_validate(doc) for doc in docs]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") 