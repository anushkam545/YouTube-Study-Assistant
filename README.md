# 🎓 YouTube Study Assistant

An AI-powered study tool that extracts YouTube video transcripts and transforms them into summaries, study notes, PDFs, and provides intelligent Q&A using RAG (Retrieval Augmented Generation).

Built with **Python · FastAPI · Streamlit · Gemini 1.5 Flash · ChromaDB**.

---

## 🚀 Features

* **One-Time Transcript Extraction** — Fetch transcript once, cache it, and reuse across all features using video_id.
* **AI-Powered Summarization** — Get concise 3-5 key point summaries of any video.
* **Smart Study Notes** — Generate structured markdown notes with headings, bullet points, and key takeaways.
* **PDF Export** — Convert notes to professionally formatted downloadable PDFs.
* **RAG-Powered Q&A** — Ask questions about the video and get accurate answers backed by relevant transcript chunks.
* **Semantic Search** — ChromaDB embeddings enable intelligent context retrieval.
* **In-Memory Caching** — Fast repeat access without re-fetching transcripts.
* **REST API Backend** — Clean FastAPI backend with Swagger docs at `/docs`.

---

## 📁 Project Structure

```
youtube-study-assistant/
│
├── app/
│   ├── main.py              # FastAPI routes (all API endpoints)
│   ├── config.py            # Environment config with Pydantic
│   ├── cache.py             # In-memory transcript storage
│   ├── transcript.py        # YouTube transcript extraction
│   │
│   └── services/
│       ├── gemini_service.py    # Gemini API integration
│       ├── embeddings.py        # Text chunking + ChromaDB storage
│       ├── pdf_service.py       # PDF generation with ReportLab
│       └── rag.py               # RAG pipeline (retrieval + generation)
│
├── tests/
│   ├── test_api.py          # API endpoint tests
│   └── test_rag.py          # RAG pipeline tests
│
├── streamlit.py             # Streamlit frontend UI
├── requirements.txt         # Python dependencies
├── .env.example
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Core language |
| FastAPI | 0.104 | REST API backend |
| Uvicorn | 0.24 | ASGI server for FastAPI |
| Streamlit | 1.32 | Frontend UI |
| Gemini 1.5 Flash | Latest | AI summarization, notes, Q&A |
| youtube-transcript-api | 1.2.4 | Extract video transcripts |
| ChromaDB | 0.4.22 | Vector database for embeddings |
| LangChain | 0.1.0 | RAG pipeline orchestration |
| Sentence Transformers | 2.7.0 | Text embeddings (all-MiniLM-L6-v2) |
| ReportLab | 4.1.0 | PDF generation |
| Pydantic | 2.1 | Request/response validation |

---

## ⚙️ Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/youtube-study-assistant.git
cd youtube-study-assistant
```

### 2. Create and Activate a Virtual Environment

```bash
# Create the environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Your Gemini API Key

* Go to → https://aistudio.google.com/app/apikey
* Click **Create API Key** → select or create a Google Cloud project
* Copy the generated key

> 💡 If you hit quota limits (429 error), create a **new Google Cloud project** and generate a fresh key under it. Each project gets its own free tier quota.

### 5. Set Up Environment Variables

Create a `.env` file in the **root** of the project:

```
GEMINI_API_KEY=your_actual_gemini_key_here
APP_NAME=YouTube Study Assistant
DEBUG=True
```

> ⚠️ Never share or commit this file. It is already excluded via `.gitignore`.

---

## ▶️ Running the App

You need **two terminals** running simultaneously.

### Terminal 1 — Start the Backend

```bash
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Visit http://127.0.0.1:8000/docs to explore all API endpoints interactively via Swagger UI.

### Terminal 2 — Start the Frontend

```bash
streamlit run streamlit.py
```

The app will open automatically at → http://localhost:8501

---

## 🎮 How to Use

### Step 1: Extract Transcript
1. Open http://localhost:8501 in your browser
2. Paste a YouTube URL — e.g. *https://www.youtube.com/watch?v=dQw4w9WgXcQ*
3. Click **Extract & Cache Transcript**
4. Save the returned `video_id` — you'll use it for all other features

### Step 2: Use the Tools

**✨ Summarize**
- Click **Summarize Video** to get 3-5 key points

**📚 Notes & PDF**
- Enter an optional video title
- Click **Generate Notes + PDF**
- Download the formatted PDF or view markdown notes

**🔍 RAG Chat**
- Click **Store Embeddings** (one-time setup per video)
- Ask any question about the video content
- Get accurate answers with source citations

**📄 Transcript**
- View the raw cached transcript text

---

## 🧠 How It Works

```
User pastes YouTube URL
        ↓
Backend extracts video_id + transcript (transcript.py)
        ↓
Transcript cached in memory (cache.py)
        ↓
User requests summary → Gemini processes transcript → returns key points
        ↓
User requests notes → Gemini generates structured markdown
        ↓
PDF service converts markdown → styled PDF with ReportLab
        ↓
User requests RAG setup → transcript chunked → embedded → stored in ChromaDB
        ↓
User asks question → retriever finds relevant chunks → Gemini generates answer
        ↓
Answer returned with source citations
```

---

## 📝 API Architecture

The app uses a **centralized transcript flow** to minimize redundant API calls:

* **POST /api/transcript** — Extract once, returns video_id
* **POST /api/summarize** — Uses cached transcript (requires video_id)
* **POST /api/notes** — Uses cached transcript (requires video_id)
* **POST /api/notes/pdf** — Uses cached transcript + generates PDF
* **POST /api/embeddings/store** — Chunks + embeds cached transcript
* **POST /api/rag/chat** — RAG Q&A using stored embeddings

This design ensures:
- YouTube API called only once per video
- Gemini API called only when generating new content
- Fast repeat operations using cached data

---

## 🔌 API Endpoints Reference

### Transcript Management
```bash
# Extract transcript
POST /api/transcript
Body: { "youtube_url": "https://youtube.com/watch?v=..." }
Returns: { "video_id": "...", "word_count": 1234 }

# View cache
GET /api/cache
Returns: { "cached_videos": ["vid1", "vid2"], "count": 2 }

# Clear cache
DELETE /api/cache/{video_id}
```

### Content Generation
```bash
# Summarize
POST /api/summarize
Body: { "video_id": "abc123" }

# Generate notes
POST /api/notes
Body: { "video_id": "abc123", "video_title": "My Video" }

# Generate PDF
POST /api/notes/pdf
Body: { "video_id": "abc123", "video_title": "My Video" }

# Download PDF
GET /api/notes/download/{video_id}
```

### RAG System
```bash
# Store embeddings
POST /api/embeddings/store
Body: { "video_id": "abc123" }

# Query embeddings
POST /api/embeddings/query
Body: { "video_id": "abc123", "query": "...", "n_results": 3 }

# RAG chat
POST /api/rag/chat
Body: { "video_id": "abc123", "question": "...", "include_sources": true }
```

---

## 💡 Challenges & Solutions

During development, several challenges were encountered and resolved:

* **Challenge**: `ModuleNotFoundError: youtube_transcript_api` compatibility issues.
  
  **Solution**: Updated to youtube-transcript-api v1.2.4 which uses instance-based API with `.fetch()` instead of class methods.

* **Challenge**: Timeout errors (60s) when calling Gemini for long transcripts.
  
  **Solution**: Implemented model caching with `@lru_cache`, added `request_timeout=45` to Gemini init, and increased Streamlit request timeout to 120s for AI endpoints.

* **Challenge**: ChromaDB collection conflicts when re-processing videos.
  
  **Solution**: Added collection deletion before creation in `embeddings.py` to ensure clean state for each video.

* **Challenge**: PDF generation failed with special characters in transcript.
  
  **Solution**: Implemented `_escape_xml()` function to handle `&`, `<`, `>` characters and proper markdown-to-ReportLab conversion.

* **Challenge**: RAG answers were generic without relevant context.
  
  **Solution**: Increased chunk retrieval from k=3 to k=5, reduced temperature to 0.3, and added custom prompt template emphasizing context usage.

* **Challenge**: Windows PowerShell `curl` commands failing.
  
  **Solution**: Switched to `Invoke-RestMethod` (PowerShell native) for API testing.

---

## 🧪 Testing

### Run Tests

```bash
# Run all API tests
pytest tests/test_api.py -v

# Test RAG pipeline (requires running backend)
python tests/test_rag.py
```

### Manual API Testing

**On Windows PowerShell:**
```powershell
# Health check
Invoke-RestMethod http://localhost:8000/health

# Test Gemini integration
Invoke-RestMethod -Uri "http://localhost:8000/api/gemini/test" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"prompt":"say hi"}'
```

**On macOS/Linux:**
```bash
# Health check
curl http://localhost:8000/health

# Test Gemini integration
curl -X POST http://localhost:8000/api/gemini/test \
  -H "Content-Type: application/json" \
  -d '{"prompt":"say hi"}'
```

---

## 🚀 Deployment

### Deploy to Render

1. Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: youtube-study-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: PYTHON_VERSION
        value: 3.11.0
    disk:
      name: chroma-storage
      mountPath: /opt/render/project/src
      sizeGB: 1

  - type: web
    name: youtube-study-frontend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run streamlit.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: API_URL
        fromService:
          type: web
          name: youtube-study-backend
          property: url
      - key: PYTHON_VERSION
        value: 3.11.0
```

2. Update `streamlit.py` to use environment variable:

```python
import os
API = os.getenv("API_URL", "http://localhost:8000")
```

3. Push to GitHub and connect to Render
4. Set `GEMINI_API_KEY` in Render dashboard
5. Deploy both services

---

## 📦 Environment Variables

Create a `.env` file with:

```env
# Required
GEMINI_API_KEY=your_key_here

# Optional
APP_NAME=YouTube Study Assistant
DEBUG=True
```

For production (Render), set these in the dashboard environment variables section.

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is already in use
# On Windows:
netstat -ano | findstr :8000

# Use different port:
uvicorn app.main:app --reload --port 8001
```

### Gemini API errors
- **429 Quota Exceeded**: Create new Google Cloud project with fresh API key
- **404 Model Not Found**: Verify model name is `gemini-1.5-flash`
- **Timeout**: Check internet connection, increase timeout in config

### ChromaDB issues
```bash
# Clear ChromaDB storage
rm -rf ./chroma_db  # Linux/Mac
rmdir /s chroma_db  # Windows
```

### Dependencies conflicts
```bash
# Fresh install
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

---

## 📊 Performance Tips

* **Cache Hit Rate**: Re-using video_id avoids redundant transcript fetches
* **Embedding Storage**: Store embeddings once per video, reuse for multiple questions
* **Chunk Size**: Default 500 chars with 50 overlap works well for most videos
* **Model Selection**: `gemini-1.5-flash` balances speed and quality for this use case

---

## 🔒 Security Notes

* Never commit `.env` file to version control
* API key has free tier limits — monitor usage at https://aistudio.google.com
* ChromaDB storage is local — no data leaves your machine except Gemini API calls
* Transcripts cached in-memory only — cleared on server restart

---

## 📜 License

MIT License — feel free to use and modify.

---

## 🤝 Contributing

Pull requests welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit pull request with clear description

---

## 🙏 Acknowledgments

* [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) for transcript extraction
* [LangChain](https://github.com/langchain-ai/langchain) for RAG orchestration
* [ChromaDB](https://github.com/chroma-core/chroma) for vector storage
* [ReportLab](https://www.reportlab.com/) for PDF generation
* Google Gemini for AI capabilities
* [FastAPI](https://fastapi.tiangolo.com/) for backend framework
* [Streamlit](https://streamlit.io/) for rapid UI development

---

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review troubleshooting section above

---

## 🗺️ Roadmap

Future enhancements planned:
- [ ] Multi-language transcript support
- [ ] Batch processing for playlists
- [ ] Export to Notion/Obsidian
- [ ] Audio timestamp navigation
- [ ] Flashcard generation from notes
- [ ] Quiz generation based on content
- [ ] Summary comparison across multiple videos
- [ ] Persistent database instead of in-memory cache

---

**Built with ❤️ using AI-powered tools**
