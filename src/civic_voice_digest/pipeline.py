from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DigestRequest:
    audio_url: str
    source_title: str
    source_url: str | None = None
    target_language: str = "en"


@dataclass(frozen=True)
class DigestPlan:
    source_title: str
    source_url: str | None
    audio_url: str
    target_language: str
    steps: list[str]
    attribution_note: str


def build_digest_plan(request: DigestRequest) -> DigestPlan:
    return DigestPlan(
        source_title=request.source_title,
        source_url=request.source_url,
        audio_url=request.audio_url,
        target_language=request.target_language,
        steps=[
            "Transcribe the public MP3 audio with Zoom Scribe API.",
            "Extract notices, dates, target audiences, and procedures with Zoom Summarizer API.",
            f"Translate the digest to {request.target_language} with Zoom Translator API.",
            "Render Markdown and JSON outputs for the Qiita article.",
        ],
        attribution_note=(
            "Reference the original municipal page and do not redistribute the audio file itself."
        ),
    )
