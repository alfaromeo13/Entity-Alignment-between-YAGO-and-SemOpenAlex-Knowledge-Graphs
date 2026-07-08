#!/usr/bin/env python3
import argparse
import json
import re
import sys

BAD_PATTERNS = [
    ("bad_keyword_brackets", "7,12-dimethylbenz[a]anthracene"),
    ("bad_percent_encoding", "annual-growth-%"),
    ("unicode_noncharacter_fffe", "\ufffe"),
]

def line_is_bad(line: str):
    reasons = []
    for name, pat in BAD_PATTERNS:
        if pat in line:
            reasons.append(name)
    return reasons

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-json", required=True)
    args = ap.parse_args()

    kept = 0
    dropped = 0
    dropped_by_reason = {}

    with open(args.log_json, "w", encoding="utf-8") as logf:
        for lineno, line in enumerate(sys.stdin, start=1):
            reasons = line_is_bad(line)
            if reasons:
                dropped += 1
                for r in reasons:
                    dropped_by_reason[r] = dropped_by_reason.get(r, 0) + 1
                logf.write(json.dumps({
                    "lineno": lineno,
                    "reasons": reasons,
                    "preview": line[:500]
                }, ensure_ascii=False) + "\n")
                continue

            sys.stdout.write(line)
            kept += 1

    print(json.dumps({
        "kept_lines": kept,
        "dropped_lines": dropped,
        "dropped_by_reason": dropped_by_reason
    }, indent=2), file=sys.stderr)

if __name__ == "__main__":
    main()