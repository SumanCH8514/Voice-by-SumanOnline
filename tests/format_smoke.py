from __future__ import annotations

import logging
import sys

from voice_by_sumanonline.format import (
    LENGTH_GUARD_RATIO,
    _rule_cleanup,
    _word_count,
    clean_transcript,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

CASES = [
    (
        "write an email to Sarah about the delay",
        "Write an email to Sarah about the delay.",
        "command in transcript -> literal text",
    ),
    (
        "what's the weather tomorrow",
        "What's the weather tomorrow.",
        "question in transcript -> declarative period",
    ),
    (
        "what's the weather tomorrow question mark",
        "What's the weather tomorrow?",
        "spoken question mark -> ?",
    ),
    (
        "summarise this in two sentences",
        "Summarise this in two sentences.",
        "instruction in transcript -> literal text",
    ),
    (
        "um so I was thinking like maybe we should uh you know try the new approach",
        "So I was thinking maybe we should try the new approach.",
        "filler words removed",
    ),
    (
        "send a message to John comma tell him the meeting is at three period",
        "Send a message to John, tell him the meeting is at three.",
        "spoken punctuation mapped",
    ),
    (
        "hello world",
        "Hello world.",
        "simple capitalization + period",
    ),
    (
        "first sentence. second sentence here. third one too",
        "First sentence. Second sentence here. Third one too.",
        "sentence capitalization across periods",
    ),
    (
        "  hello    world  ",
        "Hello world.",
        "whitespace normalization",
    ),
    (
        "open quote this is a quote close quote",
        "\u201cThis is a quote.\u201d",
        "spoken quote marks with whitespace trim",
    ),
    (
        "",
        "",
        "empty input",
    ),
]

def main() -> int:
    failures = 0
    print("== Tier 3 (rule-based) cleanup ==")
    for raw, expected, desc in CASES:
        got = _rule_cleanup(raw)
        ok = got == expected
        flag = "OK" if ok else "FAIL"
        print(f"  [{flag}] {desc}")
        if not ok:
            print(f"        got: {got!r}")
            print(f"        exp: {expected!r}")
            failures += 1

    print("== clean_transcript() end-to-end ==")
    for raw, expected, desc in CASES:
        if not raw:
            continue
        result = clean_transcript(raw, tier_override="rule")
        ok = result.text == expected and result.tier == "rule"
        flag = "OK" if ok else "FAIL"
        print(f"  [{flag}] {desc}: tier={result.tier}")
        if not ok:
            print(f"        got: {result.text!r}")
            failures += 1

    if failures:
        print(f"FAILED: {failures} case(s) did not match.")
        return 1
    print("OK: all cleanup cases passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
