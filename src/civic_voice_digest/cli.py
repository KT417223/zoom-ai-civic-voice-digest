from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .pipeline import DigestRequest, build_digest_plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a draft processing plan for a public civic voice bulletin."
    )
    parser.add_argument("--audio-url", required=True, help="Public URL of the source audio.")
    parser.add_argument("--source-title", required=True, help="Human-readable source title.")
    parser.add_argument("--source-url", help="Source web page URL for attribution.")
    parser.add_argument("--target-language", default="en", help="Translation target language.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    request = DigestRequest(
        audio_url=args.audio_url,
        source_title=args.source_title,
        source_url=args.source_url,
        target_language=args.target_language,
    )
    plan = build_digest_plan(request)
    print(json.dumps(asdict(plan), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
