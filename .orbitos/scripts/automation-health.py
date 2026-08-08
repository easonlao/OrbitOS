"""Run OrbitOS validation and project only the managed health block."""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


START = "<!-- orbitos:system-health:start -->"
END = "<!-- orbitos:system-health:end -->"
HEADING = "## 系统健康"


def read_preserving_newlines(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_preserving_newlines(path, content):
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def health_lines(result, checked_at, receipt_code=0):
    failures = [
        line.strip()
        for line in (result.stdout + "\n" + result.stderr).splitlines()
        if re.search(r"\bFAIL(?:ED)?\b|\[FAIL\]", line, re.IGNORECASE)
    ]
    if result.returncode == 0 and receipt_code == 0:
        body = [f"- 最近检查：{checked_at}", "- 结果：校验通过。"]
    elif result.returncode == 0:
        body = [
            f"- 最近检查：{checked_at}",
            f"- 结果：结构校验通过，但运行凭证写入失败（退出码 {receipt_code}）。",
            "- 下一步：检查维护状态是否可读写、是否存在锁冲突，并重新执行 System Check。",
        ]
    else:
        body = [
            f"- 最近检查：{checked_at}",
            f"- 结果：校验失败（退出码 {result.returncode}）。",
            "- 失败项：",
        ]
        body.extend(f"  - `{item}`" for item in failures[:12])
        if not failures:
            body.append("  - 校验命令未返回可解析失败项，请查看调度器输出。")
    return "\n".join([START, *body, END])


def write_receipt(root, result, checked_at, executor):
    receipt_script = root / ".orbitos" / "scripts" / "maintenance-control.py"
    failures = [
        line.strip()
        for line in (result.stdout + "\n" + result.stderr).splitlines()
        if re.search(r"\bFAIL(?:ED)?\b|\[FAIL\]", line, re.IGNORECASE)
    ]
    command = [
        sys.executable,
        str(receipt_script),
        "--root",
        str(root),
        "receipt",
        "--kind",
        "system_check",
        "--status",
        "passed" if result.returncode == 0 else "failed",
        "--executor",
        executor,
        "--observed-at",
        checked_at,
        "--evidence",
        f"run-validation exit code {result.returncode}",
        "--validation-command",
        "python .orbitos/scripts/run-validation.py",
        "--owner-agent",
        "automation-health",
    ]
    for failure in failures[:12]:
        command.extend(["--error", failure])
    receipt_result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    if receipt_result.returncode != 0:
        print(receipt_result.stderr, end="", file=sys.stderr)
    return receipt_result.returncode


def replace_health_block(today_path, block):
    content = read_preserving_newlines(today_path)
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if pattern.search(content):
        updated = pattern.sub(block, content, count=1)
    else:
        section = f"{HEADING}\n\n{block}\n\n"
        anchor = "## 6. 来源"
        updated = content.replace(anchor, section + anchor, 1) if anchor in content else content.rstrip() + "\n\n" + section
    write_preserving_newlines(today_path, updated)


def main():
    parser = argparse.ArgumentParser(description="Run OrbitOS System Check.")
    parser.add_argument("--root", default=None, help="OrbitOS root; defaults to this script's parent root.")
    parser.add_argument("--executor", default="automation-health", help="executor recorded in the run receipt")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    validator = root / ".orbitos" / "scripts" / "run-validation.py"
    today = root / "02-时间线" / "今日.md"
    if not validator.is_file() or not today.is_file():
        print("System Check requires run-validation.py and 02-时间线/今日.md.", file=sys.stderr)
        return 2

    result = subprocess.run([sys.executable, str(validator)], cwd=root, capture_output=True, text=True, check=False)
    checked_at = datetime.now().astimezone().isoformat(timespec="seconds")
    receipt_code = write_receipt(root, result, checked_at, args.executor)
    replace_health_block(today, health_lines(result, checked_at, receipt_code))
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode if result.returncode != 0 else receipt_code


if __name__ == "__main__":
    raise SystemExit(main())
