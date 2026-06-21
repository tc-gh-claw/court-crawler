# MediaMind

MediaMind is a Flask web app for turning long-form media into reusable knowledge packs.
It is inspired by the common workflow of AI audio/video assistants: paste a link, add
transcript/subtitle text or upload a text file, then generate a structured summary,
timestamped chapters, transcript snippets, a mind map, chat answers, and Markdown export.

The UI and branding are original and do not copy any third-party product.

## Features

- Link intake for videos, podcasts, courses, meetings, and web pages
- Transcript/subtitle paste box with SRT/VTT cleanup
- Text upload support for `.txt`, `.md`, `.srt`, `.vtt`, `.json`, and `.csv`
- Structured overview, keywords, takeaways, and chapter timeline
- Transcript view with generated timecodes
- Mind-map style branch view
- Chat endpoint grounded in generated notes
- Repurposing drafts for articles, social posts, and study checklists
- Markdown export

## Current MVP behavior

This repository ships a self-contained prototype that does not require paid AI,
transcription, or media-extraction services. It uses deterministic text processing
over pasted transcripts or supported text uploads.

Raw audio/video files can be selected in the UI, but the backend currently records
metadata only. For production use, connect:

1. A media downloader/extractor for supported public URLs.
2. A speech-to-text provider for audio/video transcription.
3. An LLM provider for higher-quality abstractive summaries and chat.
4. Durable storage for generated analyses.

## Quick start

```bash
pip install -r requirements.txt
python app.py
```

Open <http://localhost:5000>.

You can click **Try sample result** to see the full workspace without providing input.

## API

### `POST /api/analyze`

Accepts either JSON or multipart form data.

JSON example:

```json
{
  "url": "https://www.youtube.com/watch?v=demo",
  "title": "Building a Media Knowledge Workflow",
  "language": "en",
  "transcript": "Paste transcript or subtitles here..."
}
```

Multipart form fields:

- `url`
- `title`
- `language`
- `transcript`
- `file` (`.txt`, `.md`, `.srt`, `.vtt`, `.json`, `.csv`)

Returns a JSON knowledge pack with:

- `overview`
- `keywords`
- `takeaways`
- `chapters`
- `transcript`
- `mind_map`
- `content_cards`

### `GET /api/demo`

Generates a sample knowledge pack.

### `POST /api/chat`

```json
{
  "id": "analysis-id",
  "question": "What are the main action items?"
}
```

### `GET /api/export/<analysis_id>.md`

Downloads a Markdown version of the analysis.

### `GET /api/health`

Returns app health metadata.

## Deployment

The app runs with Gunicorn:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

`render.yaml`, `Procfile`, and `Dockerfile` are included for common Python web
deployment targets.

## Project structure

```text
.
├── app.py                  # Flask backend and summarization logic
├── templates/index.html    # Single-page web UI
├── requirements.txt        # Python dependencies
├── Procfile                # Heroku-style process definition
├── render.yaml             # Render deployment config
└── Dockerfile              # Container build
```
