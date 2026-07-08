#!/usr/bin/env python3
import argparse
import json
import sys

BAD_INLINE_PATTERNS = [
    ("bad_percent_encoding", "annual-growth-%"),
    ("bad_keyword_brackets", "7,12-dimethylbenz[a]anthracene"),
    ("unicode_noncharacter_fffe", "\ufffe"),
    ("unicode_noncharacter_ffff", "\uffff"),
]

KEYWORD_PREFIX = "hasKeyword"

def has_bad_inline_pattern(line: str):
    reasons = []
    for name, pat in BAD_INLINE_PATTERNS:
        if pat in line:
            reasons.append(name)
    return reasons

def replace_last_semicolon_with_period(line: str) -> str:
    idx = line.rfind(";")
    if idx == -1:
        return line
    return line[:idx] + "." + line[idx+1:]

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
        "semicolon_to_period_repairs": 0,
    }

    in_keyword_block = False
    keyword_block_lines = []
    keyword_block_bad = False

    pending_line = None

    with open(args.log_json, "w", encoding="utf-8") as logf:
        for lineno, line in enumerate(sys.stdin, start=1):
            reasons = has_bad_inline_pattern(line)

            # Keyword block handling
            if (not in_keyword_block) and (KEYWORD_PREFIX in line):
                if pending_line is not None:
                    sys.stdout.write(pending_line)
                    counters["kept_lines"] += 1
                    pending_line = None

                in_keyword_block = True
                keyword_block_lines = [line]
                keyword_block_bad = bool(reasons)

                for r in reasons:
                    counters["dropped_by_reason"][r] = counters["dropped_by_reason"].get(r, 0) + 1

                if line.rstrip().endswith(";"):
                    flush_keyword_block(keyword_block_lines, keyword_block_bad, sys.stdout, logf, counters)
                    in_keyword_block = False
                    keyword_block_lines = []
                    keyword_block_bad = False
                continue

            if in_keyword_block:
                keyword_block_lines.append(line)

                for r in reasons:
                    keyword_block_bad = True
                    counters["dropped_by_reason"][r] = counters["dropped_by_reason"].get(r, 0) + 1

                if line.rstrip().endswith(";"):
                    flush_keyword_block(keyword_block_lines, keyword_block_bad, sys.stdout, logf, counters)
                    in_keyword_block = False
                    keyword_block_lines = []
                    keyword_block_bad = False
                continue

            # Outside keyword blocks: handle inline poison lines
            if reasons:
                counters["dropped_lines"] += 1
                for r in reasons:
                    counters["dropped_by_reason"][r] = counters["dropped_by_reason"].get(r, 0) + 1

                # If the dropped line ended a subject block with ".", and the previous kept
                # line ends with ";", repair the previous line so the subject closes cleanly.
                if pending_line is not None:
                    if line.rstrip().endswith(".") and pending_line.rstrip().endswith(";"):
                        pending_line = replace_last_semicolon_with_period(pending_line)
                        counters["semicolon_to_period_repairs"] += 1

                logf.write(json.dumps({
                    "kind": "dropped_line",
                    "lineno": lineno,
                    "reasons": reasons,
                    "preview": line[:500]
                }, ensure_ascii=False) + "\n")
                continue

            # Good non-keyword line
            if pending_line is not None:
                sys.stdout.write(pending_line)
                counters["kept_lines"] += 1

            pending_line = line

        # EOF cleanup
        if in_keyword_block and keyword_block_lines:
            counters["dropped_keyword_blocks"] += 1
            counters["dropped_lines"] += len(keyword_block_lines)
            logf.write(json.dumps({
                "kind": "dropped_unterminated_keyword_block",
                "num_lines": len(keyword_block_lines),
                "preview": "".join(keyword_block_lines)[:1000]
            }, ensure_ascii=False) + "\n")

        if pending_line is not None:
            sys.stdout.write(pending_line)
            counters["kept_lines"] += 1

    print(json.dumps(counters, indent=2), file=sys.stderr)

if __name__ == "__main__":
    main()