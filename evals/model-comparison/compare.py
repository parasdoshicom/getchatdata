#!/usr/bin/env python3
"""Blind and summarize paired ChatData model evaluations."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import sys


def _cases(path):
    value = json.loads(Path(path).read_text())
    if not isinstance(value, list) or not value:
        raise ValueError("cases must be a nonempty JSON list")
    ids = [case.get("id") for case in value]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("case IDs must be unique nonempty strings")
    return value


def _mask_condition_markers(content):
    """Mask explicit condition names while preserving a separate untouched copy."""
    patterns = (
        (re.compile(r"chatdata", re.IGNORECASE), "[tool name masked]"),
        (re.compile(r"unguided", re.IGNORECASE), "[condition masked]"),
    )
    masked = content
    replacements = 0
    for pattern, replacement in patterns:
        masked, count = pattern.subn(replacement, masked)
        replacements += count
    return masked, replacements


def prepare(cases_path, guided_dir, unguided_dir, output_dir, seed):
    cases = _cases(cases_path)
    entries = []
    for condition, source_dir in (("chatdata", Path(guided_dir)), ("unguided", Path(unguided_dir))):
        for case in cases:
            source = source_dir / (case["id"] + ".md")
            if not source.is_file():
                raise ValueError("missing response: " + str(source))
            content = source.read_text()
            entries.append({"condition": condition, "case_id": case["id"], "content": content})
    output = Path(output_dir)
    if output.exists():
        raise ValueError("output directory already exists")
    review = output / "review"
    originals = output / "originals"
    review.mkdir(parents=True)
    originals.mkdir()
    rng = random.Random(seed)
    rng.shuffle(entries)
    key = []
    score_items = []
    case_by_id = {case["id"]: case for case in cases}
    for index, entry in enumerate(entries, 1):
        blind_id = "response-%03d" % index
        digest = hashlib.sha256(entry["content"].encode()).hexdigest()
        masked, replacements = _mask_condition_markers(entry["content"])
        (review / (blind_id + ".md")).write_text(masked)
        original_dir = originals / entry["condition"]
        original_dir.mkdir(exist_ok=True)
        (original_dir / (entry["case_id"] + ".md")).write_text(entry["content"])
        key.append({"blind_id": blind_id, "condition": entry["condition"], "case_id": entry["case_id"],
                    "original_sha256": digest, "review_sha256": hashlib.sha256(masked.encode()).hexdigest(),
                    "condition_markers_masked": replacements})
        case = case_by_id[entry["case_id"]]
        score_items.append({"blind_id": blind_id, "case_id": entry["case_id"], "pass_criterion": case["pass"],
                            "fail_criterion": case["fail"], "passed": None, "condition_guess": None,
                            "blinding_compromised": None, "notes": ""})
    (output / "key.json").write_text(json.dumps(key, indent=2) + "\n")
    (output / "scores.json").write_text(json.dumps(score_items, indent=2) + "\n")
    return {"responses": len(entries), "cases": len(cases), "review_dir": str(review),
            "originals_dir": str(originals), "key": str(output / "key.json"), "scores": str(output / "scores.json")}


def summarize(key_path, scores_path):
    key = json.loads(Path(key_path).read_text())
    scores = json.loads(Path(scores_path).read_text())
    if {item.get("blind_id") for item in key} != {item.get("blind_id") for item in scores}:
        raise ValueError("scores must contain every blinded response exactly once")
    score_by_id = {item["blind_id"]: item for item in scores}
    if len(score_by_id) != len(scores):
        raise ValueError("duplicate blind IDs in scores")
    totals = {"chatdata": {"passed": 0, "total": 0}, "unguided": {"passed": 0, "total": 0}}
    paired = {}
    guesses_recorded = correct_guesses = compromised = 0
    for item in key:
        score = score_by_id[item["blind_id"]]
        if score.get("case_id") != item["case_id"]:
            raise ValueError("case ID changed for " + item["blind_id"])
        if type(score.get("passed")) is not bool:
            raise ValueError("reviewer must set passed to true or false for " + item["blind_id"])
        if score.get("condition_guess") not in ("chatdata", "unguided", "unknown"):
            raise ValueError("reviewer must set condition_guess to chatdata, unguided, or unknown for " + item["blind_id"])
        if type(score.get("blinding_compromised")) is not bool:
            raise ValueError("reviewer must set blinding_compromised to true or false for " + item["blind_id"])
        condition = item["condition"]
        compromised += int(score["blinding_compromised"])
        if score["condition_guess"] != "unknown":
            guesses_recorded += 1
            correct_guesses += int(score["condition_guess"] == condition)
        totals[condition]["total"] += 1
        totals[condition]["passed"] += int(score["passed"])
        paired.setdefault(item["case_id"], {})[condition] = score["passed"]
    for condition in totals:
        total = totals[condition]["total"]
        totals[condition]["pass_rate"] = totals[condition]["passed"] / total if total else None
    complete_pairs = [value for value in paired.values() if set(value) == {"chatdata", "unguided"}]
    return {
        "conditions": totals,
        "paired_cases": len(complete_pairs),
        "chatdata_only_passes": sum(value["chatdata"] and not value["unguided"] for value in complete_pairs),
        "unguided_only_passes": sum(value["unguided"] and not value["chatdata"] for value in complete_pairs),
        "both_pass": sum(value["unguided"] and value["chatdata"] for value in complete_pairs),
        "both_fail": sum(not value["unguided"] and not value["chatdata"] for value in complete_pairs),
        "blinding": {"responses_marked_compromised": compromised, "condition_guesses_recorded": guesses_recorded,
                     "correct_condition_guesses": correct_guesses},
        "interpretation": "This reports observed rubric passes for the supplied sessions. Review condition guesses and compromised blinding before interpreting differences. It does not establish general model quality or productivity lift.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--cases", default=str(Path(__file__).with_name("cases.json")))
    prep.add_argument("--chatdata", required=True, help="Directory containing case-id.md responses")
    prep.add_argument("--unguided", required=True, help="Directory containing case-id.md responses")
    prep.add_argument("--output", required=True)
    prep.add_argument("--seed", type=int, required=True)
    report = sub.add_parser("summarize")
    report.add_argument("--key", required=True)
    report.add_argument("--scores", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.cases, args.chatdata, args.unguided, args.output, args.seed)
        else:
            result = summarize(args.key, args.scores)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
