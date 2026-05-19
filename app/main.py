"""
FastAPI Application - YouTube Study Assistant
Centralized transcript flow:
  1. POST /api/transcript  →  extract + cache transcript
  2. All other endpoints   →  use video_id, pull from cache
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import settings
from app.services.transcript import get_transcript_from_url
from app import cache      # ← simple in-memory cache
from app.services.gemini_service import (
    summarize_transcript,
    answer_question,
    generate_study_notes,
    generate_response,
)
from app.services.pdf_service import generate_pdf, get_pdf_path
 

app = FastAPI(
    title="YouTube Study Assistant API",
    description="Extract once, reuse everywhere.",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper ────────────────────────────────────────────────────────────────────

def get_cached_transcript(video_id: str) -> dict:
    """
    Fetch transcript from cache.
    Raises 404 if not found — tells user to call /api/transcript first.
    """
    data = cache.get(video_id)
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Transcript not found for '{video_id}'. "
                   f"Call POST /api/transcript first with the YouTube URL.",
        )
    return data


# ── Request Models ────────────────────────────────────────────────────────────

class TranscriptRequest(BaseModel):
    youtube_url: str                    # only endpoint that needs the URL


class VideoRequest(BaseModel):
    video_id: str                       # all other endpoints use this


class NotesRequest(BaseModel):
    video_id: str
    video_title: str = "Video"


class GeminiRequest(BaseModel):
    prompt: str


class QueryRequest(BaseModel):
    video_id: str
    query: str
    n_results: int = 3


class RAGRequest(BaseModel):
    video_id: str
    question: str
    include_sources: bool = True


# ── Base Routes ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "YouTube Study Assistant API",
        "version": "4.0.0",
        "workflow": [
            "1. POST /api/transcript  →  send YouTube URL once",
            "2. Use video_id returned for all other endpoints",
        ],
        "endpoints": [
            "POST /api/transcript",
            "POST /api/summarize",
            "POST /api/notes",
            "POST /api/notes/pdf",
            "GET  /api/notes/download/{video_id}",
            "POST /api/embeddings/store",
            "POST /api/embeddings/query",
            "POST /api/rag/chat",
            "GET  /api/cache",
            "DELETE /api/cache/{video_id}",
        ],
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "youtube-study-assistant",
        "cached_videos": len(cache.all_ids()),
    }


@app.get("/api/info")
def api_info():
    return {
        "app_name": settings.APP_NAME,
        "version": "4.0.0",
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "cached_videos": cache.all_ids(),
    }


# ── Step 1: Transcript (only endpoint needing YouTube URL) ────────────────────

@app.post("/api/transcript")
def extract_transcript(request: TranscriptRequest):
    """
    STEP 1 — Send YouTube URL here once.
    Extracts transcript and stores it in memory.
    Returns video_id — use this for all other endpoints.
    """
    try:
        result = get_transcript_from_url(request.youtube_url)
        video_id = result["video_id"]

        # Store in cache — all other endpoints read from here
        cache.save(
            video_id=video_id,
            transcript=result["transcript"],
            word_count=result["word_count"],
        )

        return {
            "success": True,
            "video_id": video_id,
            "word_count": result["word_count"],
            "message": f"Transcript cached. Use video_id '{video_id}' for all other endpoints.",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Step 2+: All endpoints use video_id only ──────────────────────────────────

@app.post("/api/summarize")
def summarize_video(request: VideoRequest):
    try:
        data = get_cached_transcript(request.video_id)
        summary = summarize_transcript(data["transcript"])  
        return {"success": True, "video_id": request.video_id, "summary": summary}
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Gemini API timed out - try again")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notes")
def generate_notes(request: NotesRequest):
    """Generate markdown study notes. Requires video_id."""
    try:
        data = get_cached_transcript(request.video_id)
        notes = generate_study_notes(data["transcript"], request.video_title)
        return {
            "success": True,
            "video_id": request.video_id,
            "video_title": request.video_title,
            "notes": notes,
            "format": "markdown",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notes/pdf")
def generate_notes_pdf(request: NotesRequest):
    """Generate notes + save as PDF. Requires video_id."""
    try:
        data = get_cached_transcript(request.video_id)
        notes = generate_study_notes(data["transcript"], request.video_title)
        pdf_path = generate_pdf(
            notes=notes,
            video_id=request.video_id,
            video_title=request.video_title,
        )
        return {
            "success": True,
            "video_id": request.video_id,
            "video_title": request.video_title,
            "pdf_path": pdf_path,
            "download_url": f"/api/notes/download/{request.video_id}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/notes/download/{video_id}")
def download_notes_pdf(video_id: str):
    """Download generated PDF."""
    pdf_path = get_pdf_path(video_id)
    if not pdf_path:
        raise HTTPException(
            status_code=404,
            detail=f"No PDF found for '{video_id}'. Call POST /api/notes/pdf first.",
        )
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"study_notes_{video_id}.pdf",
        headers={"Content-Disposition": f"attachment; filename=study_notes_{video_id}.pdf"},
    )


# ── Embeddings ────────────────────────────────────────────────────────────────

@app.post("/api/embeddings/store")
def store_embeddings(request: VideoRequest):
    from app.services.embeddings import process_transcript
    """Chunk + embed + store transcript in ChromaDB. Requires video_id."""
    try:
        data = get_cached_transcript(request.video_id)
        result = process_transcript(
            video_id=request.video_id,
            transcript=data["transcript"],
        )
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/embeddings/query")
def query_embeddings(request: QueryRequest):
    from app.services.embeddings import query_chromadb
    """Semantic search over stored chunks."""
    try:
        results = query_chromadb(
            video_id=request.video_id,
            query_text=request.query,
            n_results=request.n_results,
        )
        return {
            "success": True,
            "video_id": request.video_id,
            "query": request.query,
            "results": results,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── RAG ───────────────────────────────────────────────────────────────────────

@app.post("/api/rag/chat")
def rag_chat(request: RAGRequest):
    from app.services.rag import chat_with_video
    """
    RAG answer using ChromaDB + Gemini.
    Run /api/embeddings/store first for the video.
    """
    try:
        result = chat_with_video(
            video_id=request.video_id,
            question=request.question,
            include_sources=request.include_sources,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Gemini Test ───────────────────────────────────────────────────────────────

@app.post("/api/gemini/test")
def test_gemini(request: GeminiRequest):
    """Test Gemini with a raw prompt."""
    try:
        response = generate_response(request.prompt)
        return {"success": True, "prompt": request.prompt, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Cache Management ──────────────────────────────────────────────────────────

@app.get("/api/cache")
def list_cache():
    """See all video IDs currently in memory."""
    ids = cache.all_ids()
    return {
        "cached_videos": ids,
        "count": len(ids),
    }


@app.delete("/api/cache/{video_id}")
def clear_cache(video_id: str):
    """Remove a specific video from cache."""
    if not cache.exists(video_id):
        raise HTTPException(status_code=404, detail=f"'{video_id}' not in cache.")
    cache.clear(video_id)
    return {"success": True, "message": f"'{video_id}' removed from cache."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
