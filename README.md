# Document RAG QA System

A document-based question answering API using FastAPI, LangChain, OpenAI, and ChromaDB. Supports document ingestion, semantic search, and LLM-powered answer generation with user authentication and a simple frontend UI.

---

## Features & Functionality

- **User Authentication:** Register and login with JWT-based authentication. All document and vector operations are user-specific.
- **User-Specific RAG:** All retrieval-augmented generation (RAG) operations (indexing, search, answer, delete) are isolated per user—users can only access their own documents and answers.
- **Document Upload & Indexing:** Upload PDF, DOCX, or TXT files. Each file is chunked, embedded, and indexed for semantic search.
- **Document Listing & Deletion:** List and delete your own uploaded documents. Each user only sees their own documents.
- **Question Answering:**
  - **Single Response:** Submit a question and receive a complete answer in one response.
  - **Streaming Response:** Submit a question and receive the answer as a stream of tokens (see two separate buttons in the UI).
- **Semantic Search:** Uses OpenAI embeddings and ChromaDB for fast, relevant context retrieval.
- **Frontend UI:** Simple web interface for uploading, listing, deleting documents, and asking questions (with both streaming and non-streaming options).
- **API Documentation:** Interactive docs available at `/docs`.

---

## Setup & Run

### 1. **Clone the repository**
```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

### 2. **Set up environment variables**
- Set the `OPENAI_API_KEY` in docker-compose.yml environment.
- Example for Docker Compose: edit `docker-compose.yml` and set your OpenAI API key.

### 3. **Build and start the services**
```bash
docker-compose up --build
```
- This will start both the FastAPI backend and ChromaDB vector store.
- By default, transactional/user/document metadata is stored in a local SQLite database (`app.db`).

### 4. **Access the app**
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Frontend UI: [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)

---

## API Endpoints & Testing

### **Authentication**
- **POST /register**: Register a new user
- **POST /token**: Login and get JWT token

### **Document Indexing**
- **POST /documents**
  - Upload one or more files (PDF, DOCX, TXT)
  - Each file is chunked, embedded, and indexed for the current user
  - Example (using Swagger UI or Postman):
    - Set `Authorization: Bearer <token>`
    - Upload files as `multipart/form-data` under the `files` field

### **Document Listing**
- **GET /documents**
  - Returns all documents uploaded by the current user (ID, title, etc.)
  - Requires authentication

### **Question Answering**
- **POST /query**
  - JSON body: `{ "question": "..." }`
  - Returns: `{ "answer": "...", "sources": [ ... ] }`
  - Requires authentication
- **POST /query/stream**
  - Same as `/query` but streams the answer token by token (for long responses)

### **Delete Document**
- **DELETE /documents/{doc_id}**
  - Deletes the document and all associated vectors for the current user

### **Frontend UI**
- Go to `/static/index.html` for a simple web interface to upload, list, delete, and query documents.

---

## Tools & Libraries Used

- **FastAPI**: Modern, async Python web framework for building APIs quickly and with automatic docs.
- **LangChain**: For modular LLM and vector store integration, prompt management, and streaming support.
- **OpenAI**: For embeddings (text-embedding-ada-002) and LLM (GPT-3.5/4) answer generation.
- **ChromaDB**: Open-source vector database for semantic search and document chunk storage.
- **SQLAlchemy**: ORM for user and document metadata storage.
- **SQLite**: Used as the transactional database for user and document metadata (default: `app.db`).
- **Pydantic**: For data validation and serialization (like Django serializers).
- **tiktoken**: For accurate token counting and chunking.
- **PyPDF2, python-docx**: For extracting text from PDF and DOCX files.
- **Docker Compose**: For easy multi-service setup (API + ChromaDB).

**Why these tools?**
- **FastAPI** and **Pydantic** provide type safety, Aysnc processing, speed, and automatic docs.
- **LangChain** enables robust, modular LLM and vector workflows, including streaming and prompt management.
- **ChromaDB** is a modern, production-ready vector store with user-level filtering.
- **OpenAI** provides state-of-the-art embeddings and LLMs.
- **SQLAlchemy + SQLite** provide a simple, reliable transactional database for user and document metadata.
- **Docker Compose** makes local development and deployment easy.

---

## Notes
- All document and vector operations are user-specific and require authentication.

---

## Screenshot
![image](https://github.com/user-attachments/assets/663f8f4c-3cb3-4f03-99e3-3cb549735b6d)
