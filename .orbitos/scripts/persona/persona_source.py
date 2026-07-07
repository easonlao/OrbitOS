"""Dynamic Persona Layer — shared source model.

The persona source is the single source of truth for the OrbitOS dynamic
persona layer. It lives as a runtime-local Markdown file (00-系统/09-人物档案.md)
with YAML frontmatter metadata and four clearly delimited body zones:

  1. 基线身份与类型 (baseline)        — stable; changes need user confirmation
  2. 默认偏好假设   (hypotheses)      — assumptions derived from MBTI/questionnaire
  3. 证据支撑模式   (confirmed)       — patterns backed by real behavior evidence
  4. 开放校准建议   (suggestions)     — calibration suggestions only; never auto-rewrite

Projections (collaboration prefs / state summary / direction candidates) are
derived views and must not become independent truth sources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ZONE_KEYS = ["baseline", "hypotheses", "confirmed", "suggestions"]
ZONE_HEADING_HINTS = {
    "baseline": "基线身份",
    "hypotheses": "默认偏好假设",
    "confirmed": "证据支撑",
    "suggestions": "开放校准建议",
}


def _parse_scalar(raw: str):
    raw = raw.strip()
    if raw == "" or raw == "null" or raw == "~":
        return None
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",")]
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def _parse_frontmatter(fm_lines: list[str]) -> dict:
    data: dict = {}
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val == "":
            items = []
            j = i + 1
            while j < len(fm_lines) and re.match(r"^\s+-\s+", fm_lines[j]):
                items.append(re.sub(r"^\s+-\s+", "", fm_lines[j]).strip())
                j += 1
            data[key] = items
            i = j
        else:
            data[key] = _parse_scalar(val)
            i += 1
    return data


def _serialize_frontmatter(data: dict) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, (list, tuple)):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
        elif value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


@dataclass
class PersonaSource:
    frontmatter: dict = field(default_factory=dict)
    zones: dict = field(default_factory=lambda: {k: "" for k in ZONE_KEYS})

    # ----- load / save -----
    @classmethod
    def load(cls, path: Path) -> "PersonaSource":
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            raise ValueError(f"persona source missing frontmatter: {path}")
        end = text.index("\n---", 3)
        fm_text = text[3:end]
        body = text[end + 4:]
        frontmatter = _parse_frontmatter(fm_text.splitlines())

        zones = {k: "" for k in ZONE_KEYS}
        current = None
        buf: list[str] = []
        for line in body.splitlines():
            m = re.match(r"^##\s+(.*)$", line)
            if m:
                if current is not None:
                    zones[current] = "\n".join(buf).strip()
                heading = m.group(1)
                current = None
                for key, hint in ZONE_HEADING_HINTS.items():
                    if hint in heading:
                        current = key
                        break
                buf = []
            else:
                if current is not None:
                    buf.append(line)
        if current is not None:
            zones[current] = "\n".join(buf).strip()
        return cls(frontmatter=frontmatter, zones=zones)

    def save(self, path: Path) -> None:
        path = Path(path)
        body_parts = []
        for key in ZONE_KEYS:
            hint = ZONE_HEADING_HINTS[key]
            title = {
                "baseline": "一、基线身份与类型（stable baseline）",
                "hypotheses": "二、默认偏好假设（default hypotheses）",
                "confirmed": "三、证据支撑的已确认模式（confirmed patterns）",
                "suggestions": "四、开放校准建议（open calibration suggestions）",
            }[key]
            content = (self.zones.get(key) or "").strip()
            body_parts.append(f"## {title}\n\n{content}" if content else f"## {title}\n\n（暂无）")
        body = "\n\n".join(body_parts)
        text = _serialize_frontmatter(self.frontmatter) + "\n\n" + body + "\n"
        path.write_text(text, encoding="utf-8")

    # ----- helpers -----
    @property
    def mbti_type(self) -> Optional[str]:
        return self.frontmatter.get("mbti_type")

    @property
    def baseline_status(self) -> str:
        return self.frontmatter.get("baseline_status", "pending")

    def is_source_of_truth(self) -> bool:
        return self.frontmatter.get("source_of_truth", False) is True

    def add_suggestion(self, suggestion: dict) -> None:
        """Append a calibration suggestion to zone 4 only.

        Calibration must never rewrite the stable baseline (zone 1) or the
        confirmed patterns (zone 3). This method is the only sanctioned write
        path for the calibration loop.
        """
        sid = suggestion.get("id", "sug")
        line = (
            f"- [{sid}] 观测：{suggestion.get('observation', '')} "
            f"｜冲突：{suggestion.get('contradicts', '')} "
            f"｜建议：{suggestion.get('suggestion', '')} "
            f"｜状态：{suggestion.get('status', 'open')} "
            f"｜证据：{suggestion.get('evidence', '')}"
        )
        existing = (self.zones.get("suggestions") or "").strip()
        self.zones["suggestions"] = (existing + "\n" + line).strip()

    def has_suggestion(self, sid: str) -> bool:
        return f"[{sid}]" in (self.zones.get("suggestions") or "")
