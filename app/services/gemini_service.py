"""
Gemini AI Service Module
Handles Gemini API integration using LangChain
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from functools import lru_cache

@lru_cache(maxsize=1)
def initialize_gemini():
    """Cache Gemini instance"""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY missing")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.7,
        max_output_tokens=2048,
        request_timeout=45   
    )

def generate_response(prompt: str) -> str:
    try:
        llm = initialize_gemini()  # now cached
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        raise Exception(f"Gemini error: {str(e)}")
    

def summarize_transcript(transcript: str) -> str:
    """
    Summarize YouTube transcript using Gemini
    
    Args:
        transcript: Full transcript text
    
    Returns:
        Summary of the transcript
    """
    prompt = f"""
    Summarize this YouTube video transcript in 3-5 key points:
    
    {transcript[:4000]}
    
    Provide a clear, concise summary.
    """
    
    return generate_response(prompt)


def answer_question(transcript: str, question: str) -> str:
    """
    Answer question about transcript using Gemini
    
    Args:
        transcript: Video transcript text
        question: User's question
    
    Returns:
        Answer based on transcript
    """
    prompt = f"""
    Based on this YouTube video transcript, answer the following question:
    
    Transcript:
    {transcript[:4000]}
    
    Question: {question}
    
    Answer:
    """
    
    return generate_response(prompt)


def generate_study_notes(transcript: str, video_title: str = "Video") -> str:
    """
    Generate structured study notes from transcript
    
    Args:
        transcript: Full transcript text
        video_title: Title of the video (optional)
    
    Returns:
        Structured notes in markdown format
    """
    prompt = f"""
    Create comprehensive study notes from this YouTube video transcript.
    
    Video Title: {video_title}
    
    Transcript:
    {transcript[:6000]}
    
    Format the notes in markdown with:
    
    1. Main title (# heading)
    2. Overview/Introduction section
    3. Main topics as ## headings
    4. Subtopics as ### subheadings
    5. Bullet points for key concepts
    6. Important definitions or terms in **bold**
    7. A "Key Takeaways" section at the end with 3-5 bullet points
    8. A brief "Summary" section (2-3 sentences)
    
    Make the notes clear, organized, and study-friendly.
    Focus on the most important concepts and information.
    """
    
    return generate_response(prompt)
