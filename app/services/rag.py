"""
RAG (Retrieval Augmented Generation) Module
Q&A using ChromaDB + Gemini
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from app.config import settings
import chromadb


# Initialize embeddings
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
    return _embeddings

# ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")


def get_retriever(video_id: str, k: int = 5):
    """
    Get LangChain retriever for video
    
    Args:
        video_id: YouTube video ID
        k: Number of chunks to retrieve
    
    Returns:
        LangChain retriever
    """
    collection_name = f"video_{video_id}"
    
    # Create LangChain Chroma wrapper
    vectorstore = Chroma(
        client=chroma_client,
        collection_name=collection_name,
        embedding_function=get_embeddings()
    )
    
    # Create retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )
    
    return retriever


def create_rag_chain(video_id: str, k: int = 5):
    """
    Create RAG chain with Gemini + retriever
    
    Args:
        video_id: YouTube video ID
        k: Number of chunks to retrieve
    
    Returns:
        RetrievalQA chain
    """
    # Get retriever
    retriever = get_retriever(video_id, k)
    
    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
        max_output_tokens=1024
    )
    
    # Custom prompt template
    prompt_template = """Use the following context from a YouTube video to answer the question.
If you don't know the answer based on the context, say "I cannot answer this based on the video content."

Context:
{context}

Question: {question}

Answer:"""
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    # Create RAG chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    
    return qa_chain


def ask_question_rag(video_id: str, question: str, k: int = 5):
    """
    Ask question using RAG pipeline
    
    Args:
        video_id: YouTube video ID
        question: User question
        k: Number of chunks to retrieve
    
    Returns:
        Answer with source chunks
    """
    try:
        # Create RAG chain
        qa_chain = create_rag_chain(video_id, k)
        
        # Run query
        result = qa_chain({"query": question})
        
        # Extract sources
        sources = []
        for doc in result['source_documents']:
            sources.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        
        return {
            "answer": result['result'],
            "sources": sources,
            "num_sources": len(sources)
        }
    
    except Exception as e:
        if "not found" in str(e).lower():
            raise ValueError(f"Video {video_id} not indexed. Store embeddings first.")
        raise Exception(f"RAG error: {str(e)}")


def chat_with_video(video_id: str, question: str, include_sources: bool = True):
    """
    Simple chat interface for video Q&A
    
    Args:
        video_id: YouTube video ID
        question: User question
        include_sources: Include source chunks in response
    
    Returns:
        Answer dict
    """
    result = ask_question_rag(video_id, question)
    
    response = {
        "video_id": video_id,
        "question": question,
        "answer": result['answer']
    }
    
    if include_sources:
        response['sources'] = result['sources']
        response['num_sources'] = result['num_sources']
    
    return response
