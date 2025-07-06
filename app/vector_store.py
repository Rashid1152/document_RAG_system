from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import chromadb
from typing import List, Dict, Any
import uuid

class LangChainVectorStore:
    """
    Wrapper for Chroma vector store using LangChain and OpenAI embeddings.
    Provides user-specific document chunk indexing, search, and deletion.
    """
    def __init__(self):
        """
        Initialize the Chroma vector store client and embedding function.
        """
        chroma_client = chromadb.HttpClient(host="chroma", port=8000)
        embeddings = OpenAIEmbeddings()
        self.vectorstore = Chroma(
            client=chroma_client,
            collection_name="my_collection",
            embedding_function=embeddings,
        )

    def add_document_chunks(self, chunks: List[Dict[str, Any]], user_id: int):
        """
        Add document chunks to the vector store for a specific user.
        Args:
            chunks (List[Dict[str, Any]]): List of chunk dicts with 'doc_id', 'title', 'content'.
            user_id (int): The user ID to associate with the chunks.
        Returns:
            None
        """
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [dict(chunk, user_id=user_id) for chunk in chunks]
        ids = [chunk["doc_id"] + "_" + str(uuid.uuid4()) for chunk in chunks]
        self.vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        # No persist needed for remote ChromaDB

    def search(self, query: str, user_id: int, top_k: int = 5):
        """
        Search for relevant document chunks for a user using vector similarity.
        Args:
            query (str): The search query or question.
            user_id (int): The user ID to filter results.
            top_k (int): Number of top results to return.
        Returns:
            List[Dict[str, Any]]: List of metadata dicts for the top matching chunks.
        """
        results = self.vectorstore.similarity_search_with_score(query, k=top_k, filter={"user_id": user_id})
        # results: List[Tuple[Document, score]]
        return [r[0].metadata for r in results]

    def delete_document(self, doc_id: str, user_id: int):
        """
        Delete all chunks for a given document and user from the vector store.
        Args:
            doc_id (str): The document ID to delete.
            user_id (int): The user ID to filter deletion.
        Returns:
            None
        """
        self.vectorstore.delete(where={"$and": [{"doc_id": doc_id}, {"user_id": user_id}]})
        # No persist needed for remote ChromaDB

# Provide a default instance for backward compatibility
lang_obj = LangChainVectorStore()

# Module-level API for backward compatibility
def add_document_chunks(chunks, user_id):
    """
    Add document chunks to the vector store for a specific user (module-level).
    Args:
        chunks (List[Dict[str, Any]]): List of chunk dicts.
        user_id (int): The user ID.
    Returns:
        None
    """
    return lang_obj.add_document_chunks(chunks, user_id)
def search(query, user_id, top_k=5):
    """
    Search for relevant document chunks for a user (module-level).
    Args:
        query (str): The search query.
        user_id (int): The user ID.
        top_k (int): Number of top results.
    Returns:
        List[Dict[str, Any]]: List of metadata dicts.
    """
    return lang_obj.search(query, user_id, top_k)
def delete_document(doc_id, user_id):
    """
    Delete all chunks for a given document and user from the vector store (module-level).
    Args:
        doc_id (str): The document ID.
        user_id (int): The user ID.
    Returns:
        None
    """
    return lang_obj.delete_document(doc_id, user_id) 