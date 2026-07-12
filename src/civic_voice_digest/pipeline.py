from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DigestRequest:
    audio_url: str | None
    source_title: str
    source_url: str | None = None
    transcript: str | None = None
    target_language: str = "en"


@dataclass(frozen=True)
class DigestPlan:
    source_title: str
    source_url: str | None
    audio_url: str | None
    target_language: str
    steps: list[str]
    attribution_note: str


@dataclass(frozen=True)
class Notice:
    title: str
    audience: str | None
    deadline: str | None
    procedure: str | None
    confidence_notes: str


@dataclass(frozen=True)
class Digest:
    language: str
    summary: str
    notices: list[Notice]


@dataclass(frozen=True)
class DigestResult:
    source_title: str
    source_url: str | None
    audio_url: str | None
    transcript_excerpt: str | None
    digest: Digest
    translation: Digest
    attribution_note: str


def build_digest_plan(request: DigestRequest) -> DigestPlan:
    first_step = (
        "Use the provided transcript text and skip Scribe API."
        if request.transcript
        else "Transcribe the public MP3 audio with Zoom Scribe API."
    )

    return DigestPlan(
        source_title=request.source_title,
        source_url=request.source_url,
        audio_url=request.audio_url,
        target_language=request.target_language,
        steps=[
            first_step,
            "Extract notices, dates, target audiences, and procedures with Zoom Summarizer API.",
            f"Translate the digest to {request.target_language} with Zoom Translator API.",
            "Render Markdown and JSON outputs for the Qiita article.",
        ],
        attribution_note=(
            "Reference the original municipal page and do not redistribute the audio file itself."
        ),
    )


def build_sample_digest(request: DigestRequest) -> DigestResult:
    transcript_excerpt = _excerpt(request.transcript)
    source_label = request.source_title or "声の広報サンプル"

    return DigestResult(
        source_title=source_label,
        source_url=request.source_url,
        audio_url=request.audio_url,
        transcript_excerpt=transcript_excerpt,
        digest=Digest(
            language="ja",
            summary=(
                f"{source_label}を題材に、住民向けのお知らせを短く整理したサンプルです。"
                "実API接続後は、Scribeの文字起こし結果から重要なお知らせ、対象者、期限、"
                "手続きを抽出します。"
            ),
            notices=[
                Notice(
                    title="子育て世帯向けのお知らせ",
                    audience="子育て世帯",
                    deadline="実音声から抽出予定",
                    procedure="申請方法や必要書類をSummarizer APIで抽出予定",
                    confidence_notes="これはドライラン用のサンプルです。実記事では実API出力を確認します。",
                ),
                Notice(
                    title="防災・暮らしに関するお知らせ",
                    audience="市内在住者",
                    deadline=None,
                    procedure="開催場所や問い合わせ先を抽出予定",
                    confidence_notes="固有名詞と日付は公開ページと照合します。",
                ),
            ],
        ),
        translation=Digest(
            language=request.target_language,
            summary=(
                "Sample multilingual digest for a public civic voice bulletin. "
                "After API integration, this section will contain translated notices."
            ),
            notices=[
                Notice(
                    title="Notice for households with children",
                    audience="Households with children",
                    deadline="To be extracted from source audio",
                    procedure="Application steps will be extracted by the summarization step.",
                    confidence_notes="Dry-run sample. Verify real names and dates before publishing.",
                ),
                Notice(
                    title="Disaster prevention and daily life notice",
                    audience="City residents",
                    deadline=None,
                    procedure="Locations and contact details will be extracted from the source.",
                    confidence_notes="Check place names and dates against the original municipal page.",
                ),
            ],
        ),
        attribution_note=(
            "本出力は技術検証用です。音声ファイル自体は再配布せず、元ページへのリンクと"
            "短い処理例を中心に扱います。"
        ),
    )


def render_markdown(result: DigestResult) -> str:
    lines = [
        f"# {result.source_title}",
        "",
        "## Source",
        "",
        f"- Page: {result.source_url or '-'}",
        f"- Audio: {result.audio_url or '-'}",
        "",
        "## Japanese Digest",
        "",
        result.digest.summary,
        "",
    ]

    for notice in result.digest.notices:
        lines.extend(_render_notice(notice))

    lines.extend(
        [
            "## Translated Digest",
            "",
            result.translation.summary,
            "",
        ]
    )

    for notice in result.translation.notices:
        lines.extend(_render_notice(notice))

    if result.transcript_excerpt:
        lines.extend(
            [
                "## Transcript Excerpt",
                "",
                "```text",
                result.transcript_excerpt,
                "```",
                "",
            ]
        )

    lines.extend(["## Attribution Note", "", result.attribution_note, ""])
    return "\n".join(lines)


def _render_notice(notice: Notice) -> list[str]:
    return [
        f"### {notice.title}",
        "",
        f"- Audience: {notice.audience or '-'}",
        f"- Deadline: {notice.deadline or '-'}",
        f"- Procedure: {notice.procedure or '-'}",
        f"- Notes: {notice.confidence_notes}",
        "",
    ]


def _excerpt(text: str | None, limit: int = 400) -> str | None:
    if not text:
        return None

    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized

    return f"{normalized[:limit].rstrip()}..."
