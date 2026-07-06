"""Dynamic Persona Layer — minimal visible projections.

The dynamic persona layer keeps the visible surface intentionally small.
The persona source remains the only durable source of truth, and the only
long-lived derived visible target is the local collaboration preference page.
Stable baseline changes still require user confirmation elsewhere.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from persona_source import PersonaSource  # noqa: E402

DERIVED_MARK = "（本块由动态人物档案主源自动投影，非独立真相；主源稳定基线改动需经用户确认）"
COLLAB_SECTION = "## 人物档案派生（投影）"


def _collect_direction_signals(source: PersonaSource) -> list[str]:
    keywords = ("输出", "方向", "内容", "项目", "知识", "候选", "值得", "信号", "闪光", "潜力")
    signals: list[str] = []
    for zone in ("confirmed", "hypotheses"):
        for line in (source.zones.get(zone) or "").splitlines():
            line = line.strip()
            if line.startswith("-") and any(k in line for k in keywords):
                signals.append(line.lstrip("- ").strip())
    return signals


def project_collaboration(source: PersonaSource, collab_path: Path) -> bool:
    """Append/update a derived collaboration block in the local collab prefs.

    Returns True if the file was modified.
    """
    collab_path = Path(collab_path)
    if not collab_path.is_file():
        return False

    bullets = []
    for zone in ("confirmed", "hypotheses"):
        for line in (source.zones.get(zone) or "").splitlines():
            line = line.strip()
            if line.startswith("-") and any(
                k in line for k in ("协作", "沟通", "节奏", "产出", "偏好")
            ):
                bullets.append(f"- {line.lstrip('- ').strip()}（派生，假设级，待行为证据复核）")

    if not bullets:
        return False

    block = COLLAB_SECTION + "\n\n" + DERIVED_MARK + "\n\n" + "\n".join(bullets) + "\n"
    text = collab_path.read_text(encoding="utf-8")
    if COLLAB_SECTION in text:
        # replace existing derived block up to the next '## ' heading (or EOF)
        new_text = re.sub(
            re.escape(COLLAB_SECTION) + r".*?(?=\n## )",
            block.rstrip("\n"),
            text,
            flags=re.DOTALL,
        )
    else:
        new_text = text.rstrip() + "\n\n" + block

    collab_path.write_text(new_text, encoding="utf-8")
    return True


def run_projections(source, runtime: Path) -> bool:
    """Project persona conclusions into the minimal visible surface.

    The current user-facing design keeps only two long-lived visible files:
    the persona source and the local collaboration preference page.
    Separate state / direction Markdown pages are intentionally not generated.
    """
    if isinstance(source, (str, Path)):
        source = PersonaSource.load(Path(source))
    runtime = Path(runtime)
    if not source.is_source_of_truth():
        raise ValueError("target file is not marked as persona source_of_truth")
    changed = False
    changed |= project_collaboration(source, runtime / "00-系统" / "08-本地协作偏好.md")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Project persona conclusions into minimal visible targets.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--runtime", required=True, help="OrbitOS runtime root")
    parser.add_argument("--all", action="store_true", help="reserved for compatibility; currently equals collaboration projection")
    parser.add_argument("--collab", action="store_true")
    parser.add_argument("--state", action="store_true", help="deprecated no-op; separate state pages are no longer generated")
    parser.add_argument("--direction", action="store_true", help="deprecated no-op; separate direction pages are no longer generated")
    args = parser.parse_args()

    source = PersonaSource.load(Path(args.source))
    runtime = Path(args.runtime)
    if not source.is_source_of_truth():
        raise ValueError("target file is not marked as persona source_of_truth")

    do_all = args.all or not (args.collab or args.state or args.direction)
    changed = False
    if args.collab or do_all:
        changed |= project_collaboration(
            source, runtime / "00-系统" / "08-本地协作偏好.md"
        )

    print(f"projections done (collab_modified={changed}, separate_pages_generated=False)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
