"""
Phase 6 RAG Test Script
"""

import requests

BASE_URL = "http://localhost:8000"
VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_rag_pipeline():
    """Complete RAG test"""
    
    # Step 1: Store embeddings
    print("1. Storing embeddings...")
    store_response = requests.post(
        f"{BASE_URL}/api/embeddings/store",
        json={
            "youtube_url": VIDEO_URL,
            "video_title": "Test Video"
        }
    )
    
    if store_response.status_code != 200:
        print(f"Error: {store_response.json()}")
        return
    
    store_data = store_response.json()
    video_id = store_data['data']['video_id']
    print(f"✓ Stored {store_data['data']['num_chunks']} chunks")
    
    # Step 2: Ask question with RAG
    print("\n2. Asking question with RAG...")
    rag_response = requests.post(
        f"{BASE_URL}/api/rag/chat",
        json={
            "video_id": video_id,
            "question": "What is the main topic of this video?",
            "include_sources": True
        }
    )
    
    if rag_response.status_code != 200:
        print(f"Error: {rag_response.json()}")
        return
    
    rag_data = rag_response.json()
    print(f"\nQuestion: {rag_data['data']['question']}")
    print(f"\nAnswer: {rag_data['data']['answer']}")
    print(f"\nSources used: {rag_data['data']['num_sources']}")
    
    # Step 3: Show sources
    print("\n3. Source chunks:")
    for i, source in enumerate(rag_data['data']['sources'][:2]):
        print(f"\n--- Source {i+1} ---")
        print(source['content'][:200] + "...")


def test_multiple_questions():
    """Test multiple questions on same video"""
    
    video_id = "dQw4w9WgXcQ"  # Assumes already stored
    
    questions = [
        "What are the key points?",
        "Summarize the main idea",
        "What is explained in the video?"
    ]
    
    for q in questions:
        response = requests.post(
            f"{BASE_URL}/api/rag/chat",
            json={
                "video_id": video_id,
                "question": q,
                "include_sources": False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nQ: {q}")
            print(f"A: {data['data']['answer'][:150]}...")


if __name__ == "__main__":
    print("=== RAG Pipeline Test ===\n")
    test_rag_pipeline()
    
    print("\n\n=== Multiple Questions Test ===")
    test_multiple_questions()
