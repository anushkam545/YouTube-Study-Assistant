"""
YouTube Transcript Extraction Module
Compatible with youtube-transcript-api >= 1.0.0
"""

from youtube_transcript_api import YouTubeTranscriptApi
import re


def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL - could not extract video ID")


def get_transcript(video_id: str) -> str:
    # v1.x uses instance-based API with .fetch()
    ytt = YouTubeTranscriptApi()

    # Attempt 1: English
    try:
        data = ytt.fetch(video_id, languages=['en'])
        return " ".join([snippet.text for snippet in data])
    except Exception:
        pass

    # Attempt 2: Auto-generated English
    try:
        data = ytt.fetch(video_id, languages=['a.en', 'en-US', 'en-GB'])
        return " ".join([snippet.text for snippet in data])
    except Exception:
        pass

    # Attempt 3: Any available language
    try:
        data = ytt.fetch(video_id)
        return " ".join([snippet.text for snippet in data])
    except Exception as e:
        raise Exception(f"Could not fetch transcript: {str(e)}")


def get_transcript_from_url(url: str) -> dict:
    video_id = extract_video_id(url)
    transcript_text = get_transcript(video_id)
    return {
        "video_id": video_id,
        "transcript": transcript_text,
        "word_count": len(transcript_text.split())
    }