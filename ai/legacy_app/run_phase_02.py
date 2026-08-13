"""Run Phase 2 with the real OpenAI API.

Usage:
    OPENAI_API_KEY=... python3 -m app.run_phase_02 app/sample_input.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .risk_segments import AgentError, analyze_risk_segments


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze SilentGuard risk segments")
    parser.add_argument("input_file", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input_file.read_text(encoding="utf-8"))
        result = analyze_risk_segments(payload)
    except (OSError, json.JSONDecodeError, AgentError) as exc:
        print(f"FAILED: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
