"""Run the Phase 1 input-contract check locally.

Usage:
    python3 -m app.run_phase_01 app/sample_input.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contract import ContractError, validate_agent_input


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a SilentGuard Agent input JSON")
    parser.add_argument("input_file", type=Path)
    args = parser.parse_args()

    try:
        payload = json.loads(args.input_file.read_text(encoding="utf-8"))
        validated = validate_agent_input(payload)
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"INVALID: {exc}")
        return 1

    print("VALID")
    print(json.dumps(validated, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
