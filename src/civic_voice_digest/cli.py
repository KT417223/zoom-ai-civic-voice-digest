from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .pipeline import DigestRequest, build_digest_plan, build_sample_digest, render_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a draft processing plan for a public civic voice bulletin."
    )
    parser.add_argument("--audio-url", help="Public URL of the source audio.")
    parser.add_argument("--transcript-file", help="Existing transcript text file.")
    parser.add_argument("--source-title", required=True, help="Human-readable source title.")
    parser.add_argument("--source-url", help="Source web page URL for attribution.")
    parser.add_argument("--target-language", default="en", help="Translation target language.")
    parser.add_argument("--output-dir", help="Directory for digest.json and digest.md.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render sample digest outputs without calling external APIs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transcript = _read_text(args.transcript_file) if args.transcript_file else None

    if not args.audio_url and not transcript:
        raise SystemExit("Either --audio-url or --transcript-file is required.")

    request = DigestRequest(
        audio_url=args.audio_url,
        source_title=args.source_title,
        source_url=args.source_url,
        transcript=transcript,
        target_language=args.target_language,
    )

    if args.dry_run:
        result = build_sample_digest(request)
        if args.output_dir:
            _write_outputs(Path(args.output_dir), result)
        else:
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return

    plan = build_digest_plan(request)
    print(json.dumps(asdict(plan), ensure_ascii=False, indent=2))


def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _write_outputs(output_dir: Path, result) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "digest.json").write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "digest.md").write_text(render_markdown(result), encoding="utf-8")
    print(f"Wrote {output_dir / 'digest.json'}")
    print(f"Wrote {output_dir / 'digest.md'}")


if __name__ == "__main__":
    main()
