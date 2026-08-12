"""Scheduled Weekly Review lifecycle engine.

Runs the restricted week-boundary rollover for `02-时间线/本周.md` and keeps the
Dashboard projection and maintenance receipts consistent. It only manages the
weekly timeline files declared by `.orbitos/workflows/weekly-review.md`; it never
moves, deletes, or rewrites other user content.

Invocation:
  python .orbitos/scripts/weekly-review.py --executor {executor}

Modes:
- refresh: the current page already belongs to the current ISO week.
- rollover: the current page belongs to an earlier ISO week; archive it, create
  the current week page, link the previous archive, then continue.
- bootstrap: the current page is still the untouched init-runtime template.
- blocked: the task cannot continue safely; the blocked path writes exactly one
  failed receipt and a `weekly-review` blocked maintenance item to
  `.orbitos/state/maintenance.json`, then refreshes the existing Dashboard
  "需要用户决定 / 当前维护事项" entrance. Content is left untouched.

Exit codes: 0 on success, 2 when the task is safely blocked.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path


WEEK_PATTERN = re.compile(r"(?<![\w-])(\d{4}-W\d{2})")
TEMPLATE_PERIOD_MARKER = "首次 weekly-review 后更新"
BLOCK_ITEM_ID = "weekly-review"
VALIDATION_COMMAND = "python .orbitos/scripts/run-validation.py"

REASON_SOURCE_UNREADABLE = "source_unreadable"
REASON_UNKNOWN_WEEK = "unknown_week"
REASON_FUTURE_WEEK = "future_week"
REASON_ARCHIVE_CONFLICT = "archive_conflict"
REASON_VALIDATION_FAILED = "validation_failed"
REASON_WRITE_FAILED = "write_failed"

NEXT_ACTION_BLOCKED = "检查阻塞原因并修复后重新运行 Scheduled Weekly Review"


class WeeklyReviewBlocked(Exception):
    def __init__(self, reason, detail, page_week=None, stage=None):
        self.reason = reason
        self.detail = detail
        self.page_week = page_week
        self.stage = stage
        super().__init__(detail)


def now_text():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def iso_week_key(ref_date):
    iso = ref_date.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def week_range(ref_date):
    monday = ref_date - timedelta(days=ref_date.weekday())
    return monday, monday + timedelta(days=6)


def read_preserving_newlines(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    try:
        os.replace(temp_path, path)
    except BaseException:
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise


def parse_page_week(page_text):
    match = WEEK_PATTERN.search(page_text)
    return match.group(1) if match else None


def run_validation(root):
    script = root / ".orbitos/scripts/run-validation.py"
    return subprocess.run(
        [sys.executable, str(script), str(root)],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def run_control(root, *args):
    script = root / ".orbitos/scripts/maintenance-control.py"
    command = [sys.executable, str(script), "--root", str(root), *args]
    result = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    payload = {}
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {}
    return result.returncode, payload, result.stderr.strip()


def control_get_item(root, maintenance_id):
    return_code, payload, _error = run_control(root, "get", "--id", maintenance_id)
    if return_code != 0:
        return None
    return payload.get("item")


def record_receipt(root, executor, agent_id, status, evidence, errors, observed_at, subject):
    command = [
        "receipt",
        "--kind",
        "weekly_review",
        "--status",
        status,
        "--executor",
        executor,
        "--observed-at",
        observed_at,
        "--evidence",
        evidence,
        "--validation-command",
        VALIDATION_COMMAND,
        "--id",
        BLOCK_ITEM_ID,
        "--subject",
        subject,
        "--owner-agent",
        agent_id,
    ]
    for error in errors:
        command.extend(["--error", error])
    return_code, payload, error = run_control(root, *command)
    if return_code != 0:
        raise RuntimeError(error or "maintenance receipt failed")
    receipt = payload.get("receipt", {})
    return receipt.get("id"), payload.get("item")


def expire_stale_block(root, agent_id):
    item = control_get_item(root, BLOCK_ITEM_ID)
    if item is None:
        return None
    return_code, _payload, error = run_control(
        root,
        "expire",
        "--id",
        BLOCK_ITEM_ID,
        "--expected-revision",
        str(item.get("revision")),
        "--agent-id",
        agent_id,
    )
    if return_code != 0:
        return f"expire stale block failed: {error}"
    return None


def apply_block_state(root, agent_id, executor, subject, detail):
    observed_at = now_text()
    warnings = []
    try:
        _, _item = record_receipt(
            root,
            executor,
            agent_id,
            "failed",
            f"weekly review blocked: {detail}",
            [detail],
            observed_at,
            subject,
        )
    except (OSError, RuntimeError) as error:
        warnings.append(f"block receipt failed: {error}")
        return None, warnings
    item = control_get_item(root, BLOCK_ITEM_ID)
    if item is None:
        warnings.append("maintenance item could not be created after block receipt")
        return None, warnings
    return_code, _payload, error = run_control(
        root,
        "block",
        "--id",
        BLOCK_ITEM_ID,
        "--expected-revision",
        str(item.get("revision")),
        "--agent-id",
        agent_id,
        "--reason",
        detail,
    )
    if return_code != 0:
        warnings.append(f"maintenance block failed: {error}")
    return None, warnings


def refresh_projection(root, executor):
    script = root / ".orbitos/scripts/today-refresh.py"
    if not script.is_file():
        return "today-refresh.py is missing; Dashboard projection was not refreshed"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(root), "--executor", executor],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode not in (0, 1):
        return result.stderr.strip() or "Dashboard projection refresh failed"
    return None


def build_current_page(week_key, monday, sunday, created, prev_link):
    lines = [
        "---",
        "title: 本周洞察",
        "area: timeline",
        "purpose: status",
        "lifecycle: active",
        f"created: {created}",
        f"updated: {created}",
        "tags:",
        "  - orbitos",
        "  - weekly",
        "---",
        "",
        "# 本周洞察",
        "",
        f"> 周期：{week_key}（{monday.isoformat()} 至 {sunday.isoformat()}）",
    ]
    if prev_link:
        lines.append(prev_link)
    lines.extend(
        [
            "",
            "## 本周主线",
            "",
            "- 待 weekly-review 写入。",
            "",
            "## 事件时间线",
            "",
            "- 待 weekly-review 写入。",
            "",
            "## 关键洞察",
            "",
            "- 待 weekly-review 写入。",
            "",
            "## 本周已落地",
            "",
            "- 待 weekly-review 写入。",
            "",
            "## 风险与阻塞",
            "",
            "- 待 weekly-review 写入。",
            "",
            "## 下周聚焦",
            "",
            "- 待 weekly-review 写入。",
            "",
            "## 来源",
            "",
            "- [[今日]]",
        ]
    )
    return "\n".join(lines) + "\n"


def run_engine(root, args):
    ref_date = date.fromisoformat(args.date)
    target_week = iso_week_key(ref_date)
    monday, sunday = week_range(ref_date)
    current_path = root / "02-时间线/本周.md"

    if not current_path.is_file():
        raise WeeklyReviewBlocked(
            REASON_SOURCE_UNREADABLE,
            f"02-时间线/本周.md 缺失或不可读：{current_path.relative_to(root)}",
        )
    try:
        page_text = read_preserving_newlines(current_path)
    except OSError as error:
        raise WeeklyReviewBlocked(
            REASON_SOURCE_UNREADABLE,
            f"02-时间线/本周.md 读取失败：{error}",
        )

    page_week = parse_page_week(page_text)
    is_template = TEMPLATE_PERIOD_MARKER in page_text
    if page_week is None and not is_template:
        raise WeeklyReviewBlocked(
            REASON_UNKNOWN_WEEK,
            "无法从 02-时间线/本周.md 识别当前页面所属 ISO 周",
        )
    if page_week is not None and page_week > target_week:
        raise WeeklyReviewBlocked(
            REASON_FUTURE_WEEK,
            f"02-时间线/本周.md 属于未来周 {page_week}，拒绝覆盖 {target_week}",
            page_week=page_week,
        )

    if not args.skip_validation:
        validation_result = run_validation(root)
        if validation_result.returncode != 0:
            raise WeeklyReviewBlocked(
                REASON_VALIDATION_FAILED,
                "validation preflight 未通过，不做部分 rollover",
                page_week=page_week,
                stage="preflight",
            )

    if page_week == target_week:
        mode = "refresh"
        archive_path = None
    else:
        if page_week is None:
            mode = "bootstrap"
            archive_path = None
        else:
            mode = "rollover"
            archive_path = root / "02-时间线/归档" / f"{page_week}.md"
            if archive_path.exists():
                existing = read_preserving_newlines(archive_path)
                if existing != page_text:
                    raise WeeklyReviewBlocked(
                        REASON_ARCHIVE_CONFLICT,
                        f"归档 {archive_path.relative_to(root)} 已存在且内容不同，不覆盖",
                        page_week=page_week,
                    )
            else:
                try:
                    write_atomic(archive_path, page_text)
                except OSError as error:
                    raise WeeklyReviewBlocked(
                        REASON_WRITE_FAILED,
                        f"写入归档失败：{error}",
                        page_week=page_week,
                        stage="archive",
                    )
        if mode == "rollover":
            prev_link = f"> 上一周：[[归档/{page_week}|{page_week}]]"
        else:
            prev_week = iso_week_key(monday - timedelta(days=1))
            prev_archive = root / "02-时间线/归档" / f"{prev_week}.md"
            prev_link = f"> 上一周：[[归档/{prev_week}|{prev_week}]]" if prev_archive.is_file() else None
        current_page = build_current_page(
            target_week, monday, sunday, ref_date.isoformat(), prev_link
        )
        try:
            write_atomic(current_path, current_page)
        except OSError as error:
            raise WeeklyReviewBlocked(
                REASON_WRITE_FAILED,
                f"写入 02-时间线/本周.md 失败：{error}",
                page_week=page_week,
                stage="current",
            )

    if not args.skip_validation:
        validation_result = run_validation(root)
        if validation_result.returncode != 0:
            raise WeeklyReviewBlocked(
                REASON_VALIDATION_FAILED,
                "rollover 后 validation 未通过，数据已保留在归档",
                page_week=page_week,
                stage="post",
            )

    result = {
        "ok": True,
        "mode": mode,
        "current_page_week": target_week,
        "target_iso_week": target_week,
        "ran_at": now_text(),
        "warnings": [],
    }
    if archive_path is not None:
        result["archive_path"] = archive_path.relative_to(root).as_posix()
    return result


def main():
    parser = argparse.ArgumentParser(description="Run Scheduled Weekly Review lifecycle.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--executor", default="scheduled-weekly-review")
    parser.add_argument("--agent-id", default="weekly-review")
    parser.add_argument("--date", default=None, help="ISO week reference date (YYYY-MM-DD); defaults to today")
    parser.add_argument("--skip-validation", action="store_true", help="skip validation preflight/post check")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    if args.date is None:
        args.date = date.today().isoformat()
    target_week = iso_week_key(date.fromisoformat(args.date))

    if not (root / ".orbitos").is_dir():
        result = {
            "ok": False,
            "mode": "blocked",
            "blocked": {
                "current_page_week": None,
                "target_iso_week": target_week,
                "reason": REASON_SOURCE_UNREADABLE,
                "stage": None,
                "ran_at": now_text(),
                "next_action": NEXT_ACTION_BLOCKED,
                "detail": f"{root} 不是有效的 OrbitOS 根目录",
            },
            "warnings": [],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    try:
        result = run_engine(root, args)
    except WeeklyReviewBlocked as error:
        result = {
            "ok": False,
            "mode": "blocked",
            "blocked": {
                "current_page_week": error.page_week,
                "target_iso_week": target_week,
                "reason": error.reason,
                "stage": error.stage,
                "ran_at": now_text(),
                "next_action": NEXT_ACTION_BLOCKED,
                "detail": error.detail,
            },
            "warnings": [],
        }
        _blocked_reason, warnings = apply_block_state(
            root,
            args.agent_id,
            args.executor,
            f"Weekly Review 阻塞：{error.detail}",
            error.detail,
        )
        result["warnings"].extend(warnings)
        projection_warning = refresh_projection(root, args.executor)
        if projection_warning:
            result["warnings"].append(projection_warning)
    except (OSError, RuntimeError) as error:
        result = {
            "ok": False,
            "mode": "blocked",
            "blocked": {
                "current_page_week": None,
                "target_iso_week": target_week,
                "reason": REASON_WRITE_FAILED,
                "stage": None,
                "ran_at": now_text(),
                "next_action": NEXT_ACTION_BLOCKED,
                "detail": str(error),
            },
            "warnings": [],
        }
        projection_warning = refresh_projection(root, args.executor)
        if projection_warning:
            result["warnings"].append(projection_warning)
    else:
        warnings = []
        stale_warning = expire_stale_block(root, args.agent_id)
        if stale_warning:
            warnings.append(stale_warning)
        observed_at = now_text()
        try:
            receipt_id, _item = record_receipt(
                root,
                args.executor,
                args.agent_id,
                "passed",
                f"weekly review {result['mode']}: {result['target_iso_week']}",
                [],
                observed_at,
                "Weekly Review",
            )
            result["receipt_id"] = receipt_id
        except (OSError, RuntimeError) as error:
            warnings.append(f"maintenance receipt failed: {error}")
        projection_warning = refresh_projection(root, args.executor)
        if projection_warning:
            warnings.append(projection_warning)
        result["warnings"] = warnings

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
