"""
Embeddings & Vector Storage Module
Handles text chunking, embeddings, and ChromaDB storage
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
import uuid
from typing import List, Dict

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model
    
# Initialize models
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into chunks using LangChain
    
    Args:
        text: Full transcript text
        chunk_size: Max characters per chunk
        overlap: Character overlap between chunks
    
    Returns:
        List of text chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.split_text(text)
    return chunks


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using SentenceTransformers
    
    Args:
        texts: List of text chunks
    
    Returns:
        List of embedding vectors
    """
    embeddings = get_embedding_model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def store_in_chromadb(
    video_id: str,
    chunks: List[str],
    embeddings: List[List[float]],
    metadata: Dict = None
) -> str:
    """
    Store chunks and embeddings in ChromaDB
    
    Args:
        video_id: YouTube video ID
        chunks: Text chunks
        embeddings: Embedding vectors
        metadata: Additional metadata
    
    Returns:
        Collection name
    """
    # Create or get collection
    collection_name = f"video_{video_id}"
    
    try:
        collection = chroma_client.get_collection(name=collection_name)
        chroma_client.delete_collection(name=collection_name)
    except:
        pass
    
    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"video_id": video_id}
    )
    
    # Prepare IDs and metadata
    ids = [str(uuid.uuid4()) for _ in chunks]
    
    metadatas = []
    for i, chunk in enumerate(chunks):
        meta = {
            "chunk_index": i,
            "video_id": video_id,
            "chunk_length": len(chunk)
        }
        if metadata:
            meta.update(metadata)
        metadatas.append(meta)
    
    # Add to collection
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )
    
    return collection_name


def query_chromadb(video_id: str, query_text: str, n_results: int = 3) -> Dict:
    """
    Query ChromaDB for relevant chunks
    
    Args:
        video_id: YouTube video ID
        query_text: Search query
        n_results: Number of results to return
    
    Returns:
        Query results with documents and metadata
    """
    collection_name = f"video_{video_id}"
    
    try:
        collection = chroma_client.get_collection(name=collection_name)
    except Exception as e:
        raise ValueError(f"Collection not found for video {video_id}")
    
    # Generate query embedding
    query_embedding = get_embedding_model.encode([query_text])[0].tolist()
    
    # Query collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return {
        "documents": results['documents'][0],
        "metadatas": results['metadatas'][0],
        "distances": results['distances'][0]
    }


def process_transcript(video_id: str, transcript: str, metadata: Dict = None) -> Dict:
    """
    Complete pipeline: chunk → embed → store
    
    Args:
        video_id: YouTube video ID
        transcript: Full transcript text
        metadata: Optional metadata
    
    Returns:
        Processing summary
    """
    # Chunk text
    chunks = chunk_text(transcript)
    
    # Generate embeddings
    embeddings = generate_embeddings(chunks)
    
    # Store in ChromaDB
    collection_name = store_in_chromadb(
        video_id=video_id,
        chunks=chunks,
        embeddings=embeddings,
        metadata=metadata
    )
    
    return {
        "video_id": video_id,
        "collection_name": collection_name,
        "num_chunks": len(chunks),
        "total_chars": len(transcript),
        "avg_chunk_size": len(transcript) // len(chunks) if chunks else 0
    }
