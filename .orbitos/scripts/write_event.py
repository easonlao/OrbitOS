import argparse
import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVENTS_DIR = ROOT / ".orbitos" / "logs" / "events"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
CHANGE_TYPES = {"created", "updated", "deleted", "moved", "renamed"}
THINKING_MODES = {
    "5W1H",
    "苏格拉底提问",
    "SWOT 分析",
    "第一性原理",
    "反向推导",
    "金字塔原理",
    "六顶思考帽",
    "批判性思维",
}
OUTPUT_KINDS = {"event", "markdown", "project_file", "artifact", "review_item", "knowledge_candidate", "schema", "workflow", "eval", "script", "other"}
OUTPUT_STATUSES = {"created", "updated", "unchanged", "skipped", "failed"}
KNOWLEDGE_FITS = {"applicable", "partially_applicable", "not_applicable", "no_match"}
KNOWLEDGE_OUTCOMES = {"pending", "validated", "rejected", "needs_revision"}
KNOWLEDGE_FEEDBACK_ROUTES = {"none", "experience", "project_lesson", "knowledge_draft", "knowledge_conflict", "chaos_record"}


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


def parse_thinking_mode(value):
    mode, separator, purpose = value.partition(":")
    if mode not in THINKING_MODES or not separator or not purpose.strip():
        raise argparse.ArgumentTypeError(
            "thinking mode must be MODE:PURPOSE and MODE must be a registered OrbitOS thinking mode"
        )
    return {"mode": mode, "purpose": purpose.strip()}


def parse_output(value):
    parts = value.split("|", 3)
    if len(parts) < 3 or parts[0] not in OUTPUT_KINDS or not parts[1] or parts[2] not in OUTPUT_STATUSES:
        raise argparse.ArgumentTypeError("output must use KIND|REF|STATUS[|NOTE]")
    return {"kind": parts[0], "ref": parts[1], "status": parts[2], "note": parts[3] if len(parts) == 4 and parts[3] else None}


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
    ]

    thinking = None
    if args.thinking_mode:
        thinking = {"outcome": "selected", "modes": args.thinking_mode}
    elif args.thinking_bypassed:
        thinking = {"outcome": "bypassed", "modes": []}

    inputs = [
        {"kind": "file", "ref": source, "note": "knowledge source used"}
        for source in args.knowledge_source
    ]

    event = {
        "id": f"evt_{compact_time}_{args.agent_id}_{args.slug}",
        "timestamp": timestamp,
        "actor": {
            "type": "agent",
            "name": args.agent_name or args.agent_id,
            "agent_id": args.agent_id,
            "role": args.role,
            "device": None,
        },
        "event_type": args.event_type,
        "project": args.project,
        "summary": args.summary,
        "reason": args.reason,
        "thinking_modes": [item["mode"] for item in args.thinking_mode],
        "inputs": inputs,
        "actions": [
            {
                "action": "complete_task",
                "target": args.project,
                "result": "completed",
            }
        ],
        "outputs": args.output,
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
    if args.event_type == "knowledge_use":
        event["knowledge"] = {
            "sources": args.knowledge_source,
            "fit": args.knowledge_fit,
            "outcome": args.knowledge_outcome,
            "feedback_route": args.knowledge_feedback_route,
            "feedback_ref": args.knowledge_feedback_ref,
        }
    if thinking:
        event["thinking"] = thinking
    if args.collaboration_session:
        event["collaboration"] = {
            "session_id": args.collaboration_session,
            "review_status": args.review_status,
            "reviewer_session_id": args.reviewer_session,
            "reviewer_agent_id": args.reviewer_agent,
        }
    return event


def build_parser():
    parser = argparse.ArgumentParser(
        description="Write a minimal, machine-generated OrbitOS completion receipt."
    )
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--agent-name")
    parser.add_argument("--role", choices=["coordinator", "researcher", "writer", "builder", "editor"])
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
            "knowledge_use",
            "validation_failed",
            "agent_offboarding",
        ],
    )
    parser.add_argument("--file", action="append", default=[], type=parse_file_change)
    parser.add_argument("--output", action="append", default=[], type=parse_output)
    parser.add_argument("--collaboration-session")
    parser.add_argument("--review-status", choices=["not_required", "pending", "approved", "rejected"], default="not_required")
    parser.add_argument("--reviewer-session")
    parser.add_argument("--reviewer-agent")
    parser.add_argument("--review-required", action="store_true")
    parser.add_argument("--review-item", action="append", default=[])
    parser.add_argument("--hindsight-recall", action="append", default=[])
    parser.add_argument("--hindsight-retain", action="append", default=[])
    parser.add_argument("--knowledge-source", action="append", default=[])
    parser.add_argument("--knowledge-fit", choices=sorted(KNOWLEDGE_FITS))
    parser.add_argument("--knowledge-outcome", choices=sorted(KNOWLEDGE_OUTCOMES))
    parser.add_argument("--knowledge-feedback-route", choices=sorted(KNOWLEDGE_FEEDBACK_ROUTES))
    parser.add_argument("--knowledge-feedback-ref")
    parser.add_argument("--user-content-changed", action="store_true")
    thinking_group = parser.add_mutually_exclusive_group()
    thinking_group.add_argument("--thinking-mode", action="append", default=[], type=parse_thinking_mode)
    thinking_group.add_argument("--thinking-bypassed", action="store_true")
    parser.add_argument(
        "--validation", choices=["passed", "not_required"], required=True
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
    if len(args.thinking_mode) > 2:
        parser.error("at most two thinking modes can be recorded")
    if args.collaboration_session and not args.role:
        parser.error("--collaboration-session requires --role")
    if args.collaboration_session and not args.output:
        parser.error("--collaboration-session requires at least one --output")
    if args.review_status == "approved" and (not args.reviewer_session or not args.reviewer_agent):
        parser.error("approved review status requires reviewer session and agent")
    knowledge_args_used = bool(
        args.knowledge_source
        or args.knowledge_fit
        or args.knowledge_outcome
        or args.knowledge_feedback_route
        or args.knowledge_feedback_ref
    )
    if args.event_type == "knowledge_use":
        if args.knowledge_fit is None or args.knowledge_outcome is None or args.knowledge_feedback_route is None:
            parser.error("knowledge_use requires --knowledge-fit, --knowledge-outcome, and --knowledge-feedback-route")
        if len(args.knowledge_source) > 3:
            parser.error("knowledge_use accepts at most three --knowledge-source values")
        if args.knowledge_fit == "no_match" and args.knowledge_source:
            parser.error("no_match knowledge_use must not list knowledge sources")
        if args.knowledge_fit != "no_match" and not args.knowledge_source:
            parser.error("non-no_match knowledge_use requires 1-3 --knowledge-source values")
        if args.knowledge_feedback_route == "none" and args.knowledge_feedback_ref:
            parser.error("feedback route none must not have --knowledge-feedback-ref")
        if args.knowledge_feedback_route != "none" and not args.knowledge_feedback_ref:
            parser.error("non-none feedback route requires --knowledge-feedback-ref")
    elif knowledge_args_used:
        parser.error("knowledge arguments are only valid with --event-type knowledge_use")

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
