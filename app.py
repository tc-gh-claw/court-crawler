#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaMind - AI-style audio/video knowledge assistant.

This app intentionally avoids copying any third-party product branding or UI.
It provides a self-contained MVP inspired by common media-summarization flows:
link/upload input, structured notes, transcript, mind map, chat, and export.
"""

import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse

from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

ANALYSIS_DIR = Path("analysis_cache")
ANALYSIS_DIR.mkdir(exist_ok=True)

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".srt", ".vtt", ".json", ".csv"}

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "been",
    "before",
    "but",
    "can",
    "could",
    "does",
    "each",
    "from",
    "has",
    "have",
    "how",
    "into",
    "just",
    "more",
    "most",
    "not",
    "now",
    "our",
    "out",
    "over",
    "should",
    "some",
    "than",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "through",
    "use",
    "was",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "you",
    "your",
    "一個",
    "以及",
    "可以",
    "因此",
    "如果",
    "我們",
    "或者",
    "這個",
    "這些",
    "需要",
}

PLATFORM_PATTERNS = [
    ("YouTube", re.compile(r"(youtube\.com|youtu\.be)", re.I)),
    ("Bilibili", re.compile(r"bilibili\.com", re.I)),
    ("TikTok", re.compile(r"tiktok\.com", re.I)),
    ("X / Twitter", re.compile(r"(twitter\.com|x\.com)", re.I)),
    ("Podcast", re.compile(r"(podcast|spotify\.com|xiaoyuzhoufm|apple\.com/.+podcast)", re.I)),
    ("Course", re.compile(r"(coursera|ted\.com|udemy|edx)", re.I)),
]


def normalise_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def strip_subtitle_markup(text: str) -> str:
    """Remove common VTT/SRT cue metadata while keeping spoken lines."""
    cleaned_lines = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.upper() == "WEBVTT":
            continue
        if re.fullmatch(r"\d+", line):
            continue
        if re.search(r"\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s+-->\s+\d{1,2}:\d{2}:\d{2}", line):
            continue
        cleaned_lines.append(re.sub(r"<[^>]+>", "", line))
    return normalise_whitespace(" ".join(cleaned_lines))


def split_sentences(text: str) -> List[str]:
    text = normalise_whitespace(text)
    if not text:
        return []

    pieces = re.split(r"(?<=[.!?。！？])\s+", text)
    sentences = [piece.strip(" -") for piece in pieces if len(piece.strip(" -")) > 0]
    if len(sentences) <= 1 and len(text) > 220:
        sentences = [text[i : i + 180].strip() for i in range(0, len(text), 180)]
    return sentences


def infer_platform(url: str) -> str:
    if not url:
        return "Local upload"
    for name, pattern in PLATFORM_PATTERNS:
        if pattern.search(url):
            return name
    parsed = urlparse(url)
    return parsed.netloc.replace("www.", "") if parsed.netloc else "Web link"


def title_from_url(url: str) -> str:
    parsed = urlparse(url or "")
    path = parsed.path.strip("/")
    if not path:
        return parsed.netloc or "Untitled media"
    candidate = path.split("/")[-1]
    candidate = re.sub(r"[-_]+", " ", candidate)
    candidate = re.sub(r"\.\w+$", "", candidate)
    return candidate[:80].strip().title() or parsed.netloc or "Untitled media"


def read_uploaded_text(upload) -> Dict[str, str]:
    if not upload or not upload.filename:
        return {"filename": "", "text": "", "note": ""}

    filename = upload.filename
    extension = Path(filename).suffix.lower()
    payload = upload.read()

    if extension not in SUPPORTED_TEXT_EXTENSIONS:
        return {
            "filename": filename,
            "text": "",
            "note": (
                "The file was received, but this MVP only extracts text from "
                "TXT, MD, SRT, VTT, JSON, and CSV files. Add a speech-to-text "
                "service to process raw audio/video binaries."
            ),
        }

    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return {
                "filename": filename,
                "text": strip_subtitle_markup(payload.decode(encoding)),
                "note": "",
            }
        except UnicodeDecodeError:
            continue

    return {"filename": filename, "text": "", "note": "Could not decode the uploaded text file."}


def extract_keywords(sentences: Iterable[str], limit: int = 12) -> List[str]:
    tokens = []
    for sentence in sentences:
        tokens.extend(re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}|[\u4e00-\u9fff]{2,}", sentence.lower()))
    ranked = Counter(token for token in tokens if token not in STOPWORDS)
    return [word for word, _ in ranked.most_common(limit)]


def timecode(seconds: int) -> str:
    minutes, second = divmod(max(seconds, 0), 60)
    hour, minute = divmod(minutes, 60)
    if hour:
        return f"{hour:02d}:{minute:02d}:{second:02d}"
    return f"{minute:02d}:{second:02d}"


def make_takeaways(sentences: List[str], keywords: List[str]) -> List[str]:
    if not sentences:
        return [
            "Add a transcript, subtitles, or text notes to generate a content-grounded summary.",
            "Paste a public media link to preserve source context for your notes.",
            "Connect speech-to-text and LLM providers when moving from demo mode to production.",
        ]

    scored = []
    for sentence in sentences:
        score = sum(1 for keyword in keywords[:8] if keyword.lower() in sentence.lower())
        score += min(len(sentence), 180) / 180
        scored.append((score, sentence))

    unique = []
    for _, sentence in sorted(scored, reverse=True):
        if sentence not in unique:
            unique.append(sentence)
        if len(unique) == 5:
            break
    return unique


def make_chapters(sentences: List[str], keywords: List[str]) -> List[Dict[str, str]]:
    if not sentences:
        return [
            {
                "time": "00:00",
                "title": "Awaiting transcript",
                "summary": "Upload subtitles or paste transcript text to build timestamped chapters.",
            }
        ]

    chapter_count = min(5, max(2, len(sentences)))
    chunk_size = max(1, (len(sentences) + chapter_count - 1) // chapter_count)
    chapters = []

    for index in range(0, len(sentences), chunk_size):
        chunk = sentences[index : index + chunk_size]
        chapter_keywords = extract_keywords(chunk, limit=3) or keywords[:3]
        title = " / ".join(word.title() for word in chapter_keywords[:2]) or f"Part {len(chapters) + 1}"
        chapters.append(
            {
                "time": timecode(len(chapters) * 95),
                "title": title,
                "summary": " ".join(chunk[:2])[:360],
            }
        )
        if len(chapters) >= 5:
            break

    return chapters


def make_transcript_segments(sentences: List[str], title: str, source_note: str) -> List[Dict[str, str]]:
    if not sentences:
        placeholder = source_note or (
            "No transcript was provided. This demo can still organize metadata, "
            "but real audio/video transcription requires an external ASR service."
        )
        return [{"time": "00:00", "speaker": "System", "text": placeholder}]

    return [
        {
            "time": timecode(index * 35),
            "speaker": "Speaker" if index % 4 else "Host",
            "text": sentence,
        }
        for index, sentence in enumerate(sentences[:24])
    ]


def make_mind_map(title: str, chapters: List[Dict[str, str]], keywords: List[str]) -> Dict[str, object]:
    branches = []
    for chapter in chapters:
        branch_keywords = extract_keywords([chapter["summary"]], limit=4) or keywords[:4]
        branches.append(
            {
                "label": chapter["title"],
                "children": branch_keywords[:4],
            }
        )
    return {"root": title, "branches": branches}


def make_content_cards(summary: Dict[str, object]) -> List[Dict[str, str]]:
    takeaways = summary["takeaways"]
    chapters = summary["chapters"]
    first_takeaway = takeaways[0] if takeaways else "A concise media insight."
    return [
        {
            "type": "Article outline",
            "content": "\n".join(
                [
                    f"# {summary['title']}",
                    "## Key idea",
                    first_takeaway,
                    "## Sections",
                    *[f"- {chapter['title']}: {chapter['summary'][:120]}" for chapter in chapters],
                ]
            ),
        },
        {
            "type": "Social thread",
            "content": "\n".join(f"{index + 1}. {takeaway}" for index, takeaway in enumerate(takeaways[:5])),
        },
        {
            "type": "Study checklist",
            "content": "\n".join(f"- [ ] Review: {chapter['title']}" for chapter in chapters),
        },
    ]


def build_analysis(payload: Dict[str, str], upload_info: Optional[Dict[str, str]] = None) -> Dict[str, object]:
    upload_info = upload_info or {"filename": "", "text": "", "note": ""}
    url = (payload.get("url") or "").strip()
    title = normalise_whitespace(payload.get("title") or "")
    pasted_text = payload.get("transcript") or payload.get("text") or ""
    source_text = strip_subtitle_markup(pasted_text) or upload_info.get("text", "")
    platform = infer_platform(url) if url else ("Text upload" if upload_info.get("filename") else "Workspace")

    if not title:
        title = title_from_url(url) if url else Path(upload_info.get("filename") or "Untitled media").stem

    sentences = split_sentences(source_text)
    keywords = extract_keywords(sentences or [title, url], limit=12)
    takeaways = make_takeaways(sentences, keywords)
    chapters = make_chapters(sentences, keywords)
    transcript = make_transcript_segments(sentences, title, upload_info.get("note", ""))
    overview_seed = " ".join(takeaways[:2])
    overview = (
        overview_seed
        if source_text
        else "This analysis is based on the supplied media metadata. Add subtitles or a transcript for deeper, content-grounded notes."
    )

    analysis_id = hashlib.sha256(
        json.dumps(
            {
                "url": url,
                "title": title,
                "text": source_text[:5000],
                "created": datetime.utcnow().isoformat(timespec="seconds"),
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:16]

    summary = {
        "id": analysis_id,
        "title": title,
        "url": url,
        "platform": platform,
        "language": payload.get("language") or "auto",
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "duration": timecode(max(len(transcript) * 35, len(chapters) * 95)),
        "overview": overview,
        "keywords": keywords,
        "takeaways": takeaways,
        "chapters": chapters,
        "transcript": transcript,
        "mind_map": make_mind_map(title, chapters, keywords),
        "content_cards": [],
        "source_note": upload_info.get("note", ""),
        "input_mode": "transcript" if source_text else "metadata",
    }
    summary["content_cards"] = make_content_cards(summary)
    save_analysis(summary)
    return summary


def save_analysis(summary: Dict[str, object]) -> None:
    path = ANALYSIS_DIR / f"{summary['id']}.json"
    with path.open("w", encoding="utf-8") as output:
        json.dump(summary, output, ensure_ascii=False, indent=2)


def load_analysis(analysis_id: str) -> Optional[Dict[str, object]]:
    safe_id = re.sub(r"[^a-f0-9]", "", analysis_id or "")[:16]
    if not safe_id:
        return None

    path = ANALYSIS_DIR / f"{safe_id}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as source:
        return json.load(source)


def answer_question(summary: Dict[str, object], question: str) -> Dict[str, object]:
    question = normalise_whitespace(question)
    question_terms = extract_keywords([question], limit=8)
    searchable = [
        *(segment["text"] for segment in summary.get("transcript", [])),
        *(chapter["summary"] for chapter in summary.get("chapters", [])),
        *summary.get("takeaways", []),
    ]

    matches = []
    for text in searchable:
        score = sum(1 for term in question_terms if term.lower() in text.lower())
        if score:
            matches.append((score, text))

    if matches:
        best = [text for _, text in sorted(matches, reverse=True)[:3]]
        answer = " ".join(best)
    elif question:
        answer = (
            "I could not find a direct match in this analysis. The strongest overall idea is: "
            + summary.get("overview", "")
        )
    else:
        answer = "Ask about a chapter, keyword, action item, or quote from this media analysis."

    citations = [
        {"time": segment["time"], "text": segment["text"]}
        for segment in summary.get("transcript", [])[:3]
        if any(term.lower() in segment["text"].lower() for term in question_terms)
    ]
    return {"answer": answer, "citations": citations}


def analysis_to_markdown(summary: Dict[str, object]) -> str:
    lines = [
        f"# {summary['title']}",
        "",
        f"- Platform: {summary['platform']}",
        f"- Duration: {summary['duration']}",
        f"- Source: {summary['url'] or 'Local / pasted text'}",
        f"- Created: {summary['created_at']}",
        "",
        "## Overview",
        summary["overview"],
        "",
        "## Key takeaways",
        *[f"- {item}" for item in summary["takeaways"]],
        "",
        "## Chapters",
        *[f"- `{chapter['time']}` **{chapter['title']}** - {chapter['summary']}" for chapter in summary["chapters"]],
        "",
        "## Transcript",
        *[f"- `{segment['time']}` {segment['speaker']}: {segment['text']}" for segment in summary["transcript"]],
    ]
    return "\n".join(lines) + "\n"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        payload = dict(request.form)
        upload_info = read_uploaded_text(request.files.get("file"))
    else:
        payload = request.get_json(silent=True) or {}
        upload_info = None

    summary = build_analysis(payload, upload_info)
    return jsonify(summary)


@app.route("/api/demo")
def api_demo():
    sample_text = (
        "The speaker explains how modern teams turn long videos and meetings into reusable knowledge. "
        "First, they capture source material from public links, uploads, or existing subtitles. "
        "Next, they extract a transcript and split it into chapters with timestamps. "
        "The most valuable step is transforming raw transcript text into summaries, questions, action items, and shareable drafts. "
        "A good workflow keeps citations connected to the original timecode so readers can verify every insight. "
        "Finally, the team exports the result into Markdown, Notion, Obsidian, or social posts for follow-up work."
    )
    return jsonify(
        build_analysis(
            {
                "url": "https://www.youtube.com/watch?v=demo",
                "title": "Building a Media Knowledge Workflow",
                "transcript": sample_text,
                "language": "en",
            }
        )
    )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    payload = request.get_json(silent=True) or {}
    summary = load_analysis(payload.get("id", ""))
    if not summary:
        return jsonify({"error": "Analysis not found. Generate a summary first."}), 404
    return jsonify(answer_question(summary, payload.get("question", "")))


@app.route("/api/export/<analysis_id>.md")
def api_export_markdown(analysis_id: str):
    summary = load_analysis(analysis_id)
    if not summary:
        return jsonify({"error": "Analysis not found"}), 404

    markdown = analysis_to_markdown(summary)
    filename = re.sub(r"[^A-Za-z0-9_-]+", "-", summary["title"]).strip("-").lower() or "media-summary"
    return Response(
        markdown,
        mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}.md"},
    )


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "app": "MediaMind"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
