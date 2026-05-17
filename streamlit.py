"""
YouTube Study Assistant - Streamlit UI
New flow: extract transcript once → use video_id everywhere
Run: streamlit run frontend/streamlit_app.py
"""

import streamlit as st
import requests
import os

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="YouTube Study Assistant", page_icon="🎓", layout="centered")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
.stApp { background: #0e0e16; color: #e2e2f0; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 780px; }

.app-title { font-size:2.2rem; font-weight:700; background:linear-gradient(120deg,#818cf8,#a78bfa,#38bdf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; text-align:center; margin-bottom:0.2rem; }
.app-sub { font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#4b5563; text-align:center; letter-spacing:0.08em; }

/* Step banner */
.step-box { background:#13131f; border:1px solid #1e1e30; border-radius:12px; padding:1rem 1.25rem; margin:1rem 0; }
.step-title { font-weight:700; font-size:0.9rem; color:#a78bfa; margin-bottom:0.3rem; }
.step-desc { font-family:'JetBrains Mono',monospace; font-size:0.73rem; color:#4b5563; }

/* Video ID badge */
.vid-badge { display:inline-flex; align-items:center; gap:8px; background:#1a1a2e; border:1px solid #818cf8; border-radius:10px; padding:0.5rem 1rem; font-family:'JetBrains Mono',monospace; font-size:0.82rem; color:#a78bfa; margin:0.5rem 0 1rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background:#13131f; border-radius:12px; padding:4px; border:1px solid #1e1e30; gap:2px; }
.stTabs [data-baseweb="tab"] { border-radius:8px; color:#6b7280; font-weight:600; font-size:0.85rem; padding:0.45rem 1.1rem; }
.stTabs [aria-selected="true"] { background:#1e1e38 !important; color:#a78bfa !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top:1.25rem; }

/* Inputs */
.stTextInput>div>div>input, .stTextArea>div>div>textarea { background:#13131f !important; border:1px solid #1e1e30 !important; border-radius:10px !important; color:#e2e2f0 !important; font-family:'JetBrains Mono',monospace !important; font-size:0.82rem !important; }
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus { border-color:#818cf8 !important; box-shadow:0 0 0 2px rgba(129,140,248,0.12) !important; }
label { color:#9ca3af !important; font-size:0.82rem !important; font-weight:500 !important; }

/* Buttons */
.stButton>button { background:linear-gradient(135deg,#4f46e5,#7c3aed) !important; color:#fff !important; border:none !important; border-radius:10px !important; font-family:'Outfit',sans-serif !important; font-weight:600 !important; font-size:0.87rem !important; padding:0.55rem 1.4rem !important; width:100% !important; transition:opacity .2s !important; }
.stButton>button:hover { opacity:0.85 !important; }
.stDownloadButton>button { background:linear-gradient(135deg,#065f46,#047857) !important; color:#fff !important; border:none !important; border-radius:10px !important; font-family:'Outfit',sans-serif !important; font-weight:600 !important; width:100% !important; }

/* Result card */
.result-card { background:#13131f; border:1px solid #1e1e30; border-left:3px solid #818cf8; border-radius:12px; padding:1.2rem 1.4rem; margin-top:0.75rem; font-family:'JetBrains Mono',monospace; font-size:0.8rem; line-height:1.75; color:#c4c4d8; white-space:pre-wrap; word-break:break-word; }
.result-card.green { border-left-color:#34d399; }
.result-card.amber { border-left-color:#fbbf24; }
.result-card.red   { border-left-color:#f87171; color:#f87171; }

.pill-row { display:flex; gap:8px; flex-wrap:wrap; margin:0.5rem 0; }
.pill { background:rgba(129,140,248,0.08); border:1px solid rgba(129,140,248,0.2); color:#818cf8; font-family:'JetBrains Mono',monospace; font-size:0.7rem; padding:0.18rem 0.6rem; border-radius:6px; }
.pill.green { background:rgba(52,211,153,0.08); border-color:rgba(52,211,153,0.2); color:#34d399; }

.sec-label { font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#818cf8; letter-spacing:0.12em; text-transform:uppercase; margin:0.8rem 0 0.3rem; }
hr { border-color:#1a1a2a; margin:1rem 0; }
.stSpinner>div { border-top-color:#818cf8 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def post(endpoint, payload, timeout=60):
    # AI endpoints need more time
    if any(x in endpoint for x in ['/summarize', '/notes', '/rag']):
        timeout = 120
    
    try:
        r = requests.post(f"{API}{endpoint}", json=payload, timeout=timeout)
        return r.json(), r.status_code
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {timeout}s"}, 504
    except requests.exceptions.ConnectionError:
        return {"error": "Backend offline"}, 503
    except Exception as e:
        return {"error": str(e)}, 500

def get(endpoint, timeout=30):
    try:
        r = requests.get(f"{API}{endpoint}", timeout=timeout)
        return r, r.status_code
    except Exception as e:
        return None, 500

def is_online():
    try:
        requests.get(f"{API}/health", timeout=2)
        return True
    except:
        return False

def result(text, color=""):
    st.markdown(f'<div class="result-card {color}">{text}</div>', unsafe_allow_html=True)

def label(text):
    st.markdown(f'<div class="sec-label">{text}</div>', unsafe_allow_html=True)

def pills(items, color=""):
    html = '<div class="pill-row">' + "".join(f'<span class="pill {color}">{i}</span>' for i in items) + '</div>'
    st.markdown(html, unsafe_allow_html=True)

def show_vid_badge(video_id):
    st.markdown(f'<div class="vid-badge">🎬 video_id: <b>{video_id}</b></div>', unsafe_allow_html=True)

def need_transcript_warning():
    st.markdown('<div class="result-card red">⚠ No transcript loaded yet.\nGo to Step 1 and extract a transcript first.</div>', unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
online = is_online()
dot = "🟢" if online else "🔴"

st.markdown(f'<div class="app-title">🎓 YouTube Study Assistant</div>', unsafe_allow_html=True)
st.markdown(f'<div class="app-sub">{dot} backend {"online" if online else "offline"} &nbsp;·&nbsp; extract once · reuse everywhere</div>', unsafe_allow_html=True)
st.markdown("")

# ── STEP 1 — Extract Transcript ───────────────────────────────────────────────
st.markdown("""
<div class="step-box">
    <div class="step-title">Step 1 — Extract Transcript</div>
    <div class="step-desc">Paste a YouTube URL once. All tabs below use the video_id automatically.</div>
</div>
""", unsafe_allow_html=True)

url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")

if st.button("Extract & Cache Transcript"):
    if not url.strip():
        st.warning("Paste a YouTube URL.")
    else:
        with st.spinner("Fetching transcript..."):
            data, status = post("/api/transcript", {"youtube_url": url})
        if status == 200 and data.get("success"):
            st.session_state.video_id = data["video_id"]
            st.session_state.word_count = data["word_count"]
            st.success(f"✓ Transcript cached — {data['word_count']:,} words")
        else:
            st.error(data.get("detail") or data.get("error"))

# Show active video badge
if "video_id" in st.session_state:
    show_vid_badge(st.session_state.video_id)
    pills([f"words: {st.session_state.get('word_count', '?'):,}"], "green")

st.markdown("---")

# ── STEP 2 — Tabs ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="step-box">
    <div class="step-title">Step 2 — Use the Tools</div>
    <div class="step-desc">All tabs below use the cached transcript automatically. No URL needed again.</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "✨  Summarize",
    "📚  Notes & PDF",
    "🔍  RAG Chat",
    "📄  Transcript",
])


# ── TAB 1 — SUMMARIZE ─────────────────────────────────────────────────────────
with tab1:
    if "video_id" not in st.session_state:
        need_transcript_warning()
    else:
        vid = st.session_state.video_id

        if st.button("Summarize Video", key="btn_sum"):
            with st.spinner("Summarizing..."):
                data, status = post("/api/summarize", {"video_id": vid})
            if status == 200 and data.get("success"):
                label("summary")
                result(data["summary"], "green")
            else:
                st.error(data.get("detail") or data.get("error"))
        
        st.markdown("---")
        st.info("💡 For Q&A, use the RAG Chat tab →")


# ── TAB 2 — NOTES & PDF ───────────────────────────────────────────────────────
with tab2:
    if "video_id" not in st.session_state:
        need_transcript_warning()
    else:
        vid = st.session_state.video_id
        title = st.text_input("Video title (optional)", placeholder="My Video", key="n_title")

        if st.button("Generate Notes + PDF", key="btn_notes"):
            with st.spinner("Generating notes and building PDF..."):
                data, status = post("/api/notes/pdf", {
                    "video_id": vid,
                    "video_title": title.strip() or "Video",
                })
            if status == 200 and data.get("success"):
                pills([f"video_id: {vid}", "saved as PDF"], "green")

                # Download button
                resp, s = get(f"/api/notes/download/{vid}")
                if s == 200 and resp:
                    st.download_button(
                        "⬇  Download PDF",
                        data=resp.content,
                        file_name=f"notes_{vid}.pdf",
                        mime="application/pdf",
                    )

                # Markdown preview
                preview, _ = post("/api/notes", {
                    "video_id": vid,
                    "video_title": title.strip() or "Video",
                })
                if preview.get("success"):
                    with st.expander("View markdown notes"):
                        st.markdown(preview["notes"])
            else:
                st.error(data.get("detail") or data.get("error"))


# ── TAB 3 — RAG CHAT ──────────────────────────────────────────────────────────
with tab3:
    if "video_id" not in st.session_state:
        need_transcript_warning()
    else:
        vid = st.session_state.video_id

        if st.button("Store Embeddings", key="btn_store"):
            with st.spinner("Chunking → embedding → storing..."):
                data, status = post("/api/embeddings/store", {"video_id": vid})
            if status == 200 and data.get("success"):
                d = data["data"]
                pills([f"chunks: {d['num_chunks']}", f"avg size: {d['avg_chunk_size']} chars"], "green")
                st.success("Ready to chat!")
                st.session_state.embeddings_stored = True
            else:
                st.error(data.get("detail") or data.get("error"))

        st.markdown("---")

        q = st.text_area("Ask a question (RAG)", placeholder="What does the video say about...?", height=80, key="r_q")

        if st.button("Ask with RAG", key="btn_rag"):
            if not q.strip():
                st.warning("Type a question.")
            elif not st.session_state.get("embeddings_stored"):
                st.warning("Click 'Store Embeddings' first.")
            else:
                with st.spinner("Searching transcript chunks + generating answer..."):
                    data, status = post("/api/rag/chat", {
                        "video_id": vid,
                        "question": q,
                        "include_sources": True,
                    })
                if status == 200 and data.get("success"):
                    d = data["data"]
                    label("answer")
                    result(d["answer"], "green")
                    if d.get("sources"):
                        pills([f"sources used: {d.get('num_sources', 0)}"])
                        for i, src in enumerate(d["sources"][:2]):
                            with st.expander(f"Source chunk {i+1}"):
                                result(src["content"][:400])
                else:
                    st.error(data.get("detail") or data.get("error"))


# ── TAB 4 — RAW TRANSCRIPT ───────────────────────────────────────────────────
with tab4:
    if "video_id" not in st.session_state:
        need_transcript_warning()
    else:
        vid = st.session_state.video_id
        label("cached transcript")
        r, s = get(f"/api/cache")
        if s == 200:
            cache_data = r.json()
            pills([f"videos in cache: {cache_data['count']}"])

        # fetch and show transcript from /api/transcript endpoint won't work
        # so we store it in session on extraction
        if "transcript_text" not in st.session_state:
            st.info("Re-extract the transcript to preview it here.")
        else:
            result(st.session_state.transcript_text[:3000] + "...")