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


def health_lines(result):
    checked_at = datetime.now().astimezone().isoformat(timespec="seconds")
    failures = [
        line.strip()
        for line in (result.stdout + "\n" + result.stderr).splitlines()
        if re.search(r"\bFAIL(?:ED)?\b|\[FAIL\]", line, re.IGNORECASE)
    ]
    if result.returncode == 0:
        body = [f"- 最近检查：{checked_at}", "- 结果：校验通过。"]
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


def replace_health_block(today_path, block):
    content = today_path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if pattern.search(content):
        updated = pattern.sub(block, content, count=1)
    else:
        section = f"{HEADING}\n\n{block}\n\n"
        anchor = "## 6. 来源"
        updated = content.replace(anchor, section + anchor, 1) if anchor in content else content.rstrip() + "\n\n" + section
    today_path.write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run OrbitOS System Check.")
    parser.add_argument("--root", default=None, help="OrbitOS root; defaults to this script's parent root.")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    validator = root / ".orbitos" / "scripts" / "run-validation.py"
    today = root / "02-时间线" / "今日.md"
    if not validator.is_file() or not today.is_file():
        print("System Check requires run-validation.py and 02-时间线/今日.md.", file=sys.stderr)
        return 2

    result = subprocess.run([sys.executable, str(validator)], cwd=root, capture_output=True, text=True, check=False)
    replace_health_block(today, health_lines(result))
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
