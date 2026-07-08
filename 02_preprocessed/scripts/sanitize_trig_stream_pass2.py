#!/usr/bin/env python3
import argparse
import json
import sys

BAD_INLINE_PATTERNS = [
    ("bad_percent_encoding", "annual-growth-%"),
    ("bad_keyword_brackets", "7,12-dimethylbenz[a]anthracene"),
    ("unicode_noncharacter_fffe", "\ufffe"),
]

KEYWORD_PREFIX = "hasKeyword"
OPENALEX_KEYWORD_PREFIX = "<https://openalex.org/keywords/"

def has_bad_inline_pattern(line: str):
    reasons = []
    for name, pat in BAD_INLINE_PATTERNS:
        if pat in line:
            reasons.append(name)
    return reasons

def flush_keyword_block(block_lines, block_bad, out, logf, counters):
    if not block_lines:
        return
    if block_bad:
        counters["dropped_keyword_blocks"] += 1
        counters["dropped_lines"] += len(block_lines)
        logf.write(json.dumps({
            "kind": "dropped_keyword_block",
            "num_lines": len(block_lines),
            "preview": "".join(block_lines)[:1000]
        }, ensure_ascii=False) + "\n")
    else:
        for ln in block_lines:
            out.write(ln)
            counters["kept_lines"] += 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-json", required=True)
    args = ap.parse_args()

    counters = {
        "kept_lines": 0,
        "dropped_lines": 0,
        "dropped_by_reason": {},
        "dropped_keyword_blocks": 0,
    }

    in_keyword_block = False
    keyword_block_lines = []
    keyword_block_bad = False

    with open(args.log_json, "w", encoding="utf-8") as logf:
        for lineno, line in enumerate(sys.stdin, start=1):
            reasons = has_bad_inline_pattern(line)

            # Start of a hasKeyword predicate block
            if (not in_keyword_block) and (KEYWORD_PREFIX in line):
                in_keyword_block = True
                keyword_block_lines = [line]
                keyword_block_bad = False

                if reasons:
                    keyword_block_bad = True
                    for r in reasons:
                        counters["dropped_by_reason"][r] = counters["dropped_by_reason"].get(r, 0) + 1

                # If block ends on same line
                if line.rstrip().endswith(";"):
                    flush_keyword_block(keyword_block_lines, keyword_block_bad, sys.stdout, logf, counters)
                    in_keyword_block = False
                    keyword_block_lines = []
                    keyword_block_bad = False
                continue

            if in_keyword_block:
                keyword_block_lines.append(line)
                if reasons:
                    keyword_block_bad = True
                    for r in reasons:
                        counters["dropped_by_reason"][r] = counters["dropped_by_reason"].get(r, 0) + 1

                if line.rstrip().endswith(";"):
                    flush_keyword_block(keyword_block_lines, keyword_block_bad, sys.stdout, logf, counters)
                    in_keyword_block = False
                    keyword_block_lines = []
                    keyword_block_bad = False
                continue

            # Outside keyword blocks: drop obvious poison lines directly
            if reasons:
                counters["dropped_lines"] += 1
                for r in reasons:
                    counters["dropped_by_reason"][r] = counters["dropped_by_reason"].get(r, 0) + 1
                logf.write(json.dumps({
                    "kind": "dropped_line",
                    "lineno": lineno,
                    "reasons": reasons,
                    "preview": line[:500]
                }, ensure_ascii=False) + "\n")
                continue

            sys.stdout.write(line)
            counters["kept_lines"] += 1

        # If file ends mid-block, flush conservatively by dropping it
        if in_keyword_block and keyword_block_lines:
            counters["dropped_keyword_blocks"] += 1
            counters["dropped_lines"] += len(keyword_block_lines)
            logf.write(json.dumps({
                "kind": "dropped_unterminated_keyword_block",
                "num_lines": len(keyword_block_lines),
                "preview": "".join(keyword_block_lines)[:1000]
            }, ensure_ascii=False) + "\n")

    print(json.dumps(counters, indent=2), file=sys.stderr)

if __name__ == "__main__":
    main()