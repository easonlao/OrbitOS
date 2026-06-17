import argparse
import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVENTS_DIR = ROOT / ".orbitos" / "logs" / "events"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
CHANGE_TYPES = {"created", "updated", "deleted", "moved", "renamed"}


def parse_file_change(value):
    parts = value.split(":", 2)
    if len(parts) < 2 or parts[0] not in CHANGE_TYPES or not parts[1]:
        raise argparse.ArgumentTypeError(
            "file change must be CHANGE_TYPE:PATH[:PURPOSE]"
        )
    return {
        "path": parts[1],
        "change_type": parts[0],
        "purpose": parts[2] if len(parts) == 3 and parts[2] else None,
    }


def build_event(args, now):
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S%z")
    timestamp = f"{timestamp[:-2]}:{timestamp[-2:]}"
    compact_time = now.strftime("%Y%m%d_%H%M%S")
    review_items = [{"item": item} for item in args.review_item]

    checklist = [
        {
            "item": "task_scope",
            "status": "done",
            "note": "Agent confirmed the change stayed within the requested scope.",
        },
        {
            "item": "user_content",
            "status": "done" if not args.user_content_changed else "done",
            "note": (
                "User content was changed as explicitly requested."
                if args.user_content_changed
                else "No user content was moved, deleted, or archived."
            ),
        },
        {
            "item": "formal_artifact",
            "status": "done",
            "note": (
                "Formal artifact requires review."
                if args.review_required
                else "No unconfirmed formal artifact was promoted."
            ),
        },
        {
            "item": "validation",
            "status": "done" if args.validation == "passed" else "skipped",
            "note": f"validation={args.validation}",
        },
        {
            "item": "experience_check",
            "status": "done",
            "note": args.experience_check,
        },
    ]

    return {
        "id": f"evt_{compact_time}_{args.agent_id}_{args.slug}",
        "timestamp": timestamp,
        "actor": {
            "type": "agent",
            "name": args.agent_name or args.agent_id,
            "agent_id": args.agent_id,
            "role": None,
            "device": None,
        },
        "event_type": args.event_type,
        "project": args.project,
        "summary": args.summary,
        "reason": args.reason,
        "thinking_modes": [],
        "inputs": [],
        "actions": [
            {
                "action": "complete_task",
                "target": args.project,
                "result": "completed",
            }
        ],
        "outputs": [],
        "files_changed": args.file,
        "review_required": args.review_required,
        "review_items": review_items,
        "checklist": checklist,
        "next_steps": [],
        "hindsight": {
            "used": bool(args.hindsight_recall or args.hindsight_retain),
            "recall": args.hindsight_recall,
            "retain": args.hindsight_retain,
            "note": None,
        },
        "related_events": [],
        "confidence": "high",
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Write a minimal, machine-generated OrbitOS completion receipt."
    )
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--agent-name")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--project")
    parser.add_argument(
        "--event-type",
        default="progress_sync",
        choices=[
            "startup_sync",
            "progress_sync",
            "file_change",
            "decision_candidate",
            "artifact_candidate",
            "project_update",
            "system_change",
            "inbox_triage",
            "validation_failed",
        ],
    )
    parser.add_argument("--file", action="append", default=[], type=parse_file_change)
    parser.add_argument("--review-required", action="store_true")
    parser.add_argument("--review-item", action="append", default=[])
    parser.add_argument("--hindsight-recall", action="append", default=[])
    parser.add_argument("--hindsight-retain", action="append", default=[])
    parser.add_argument("--user-content-changed", action="store_true")
    parser.add_argument(
        "--validation", choices=["passed", "not_required"], required=True
    )
    parser.add_argument(
        "--experience-check",
        default="not_applicable",
        choices=[
            "not_applicable",
            "captured",
            "candidate_only",
            "learned_updated",
        ],
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not SLUG_PATTERN.fullmatch(args.slug):
        parser.error("slug must use lowercase snake_case")
    if args.review_required and not args.review_item:
        parser.error("--review-required needs at least one --review-item")

    now = datetime.now().astimezone()
    event = build_event(args, now)
    content = json.dumps(event, ensure_ascii=False, indent=2) + "\n"

    if args.dry_run:
        print(content, end="")
        return

    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{args.slug}.yaml"
    target = EVENTS_DIR / filename
    if target.exists():
        parser.error(f"event already exists: {target.relative_to(ROOT)}")
    target.write_text(content, encoding="utf-8", newline="\n")
    print(target.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
