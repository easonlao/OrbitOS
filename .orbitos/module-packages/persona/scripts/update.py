"""Dynamic Persona Layer — user-confirmed update flow.

Applies user-approved updates to the runtime-local persona source. This module
never invents new facts on its own: it only records explicit user-confirmed
changes such as confirming the baseline, accepting a calibration suggestion into
confirmed patterns, or dismissing a suggestion.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from persona_source import PersonaSource  # noqa: E402
import project  # noqa: E402


def _today() -> str:
    return _dt.date.today().isoformat()


def apply_update(
    source_path: Path,
    runtime_root: Path,
    *,
    confirm_baseline: bool = False,
    identity: str | None = None,
    accept_suggestion: str | None = None,
    dismiss_suggestion: str | None = None,
    confirmed_id: str | None = None,
    confirmed_statement: str | None = None,
    evidence: str | None = None,
    note: str | None = None,
    refresh_collab: bool = True,
) -> list[str]:
    source = PersonaSource.load(Path(source_path))
    if not source.is_source_of_truth():
        raise ValueError("target file is not marked as persona source_of_truth")

    actions: list[str] = []

    if identity:
        source.set_identity(identity)
        actions.append("identity-updated")

    if confirm_baseline:
        source.set_baseline_status("confirmed")
        actions.append("baseline-confirmed")

    if accept_suggestion:
        if not confirmed_statement or not evidence:
            raise ValueError("accepting a suggestion requires confirmed_statement and evidence")
        pattern_id = confirmed_id or f"confirmed_{accept_suggestion}"
        source.add_confirmed_pattern(pattern_id, confirmed_statement, evidence)
        source.set_suggestion_status(accept_suggestion, "accepted", note)
        actions.append(f"suggestion-accepted:{accept_suggestion}")

    if dismiss_suggestion:
        source.set_suggestion_status(dismiss_suggestion, "dismissed", note)
        actions.append(f"suggestion-dismissed:{dismiss_suggestion}")

    if not actions:
        raise ValueError("no update action specified")

    source.frontmatter["updated"] = _today()
    source.save(Path(source_path))

    if refresh_collab:
        project.run_projections(source, Path(runtime_root))
        actions.append("collab-projection-refreshed")

    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply user-confirmed persona updates.")
    parser.add_argument("--source", required=True, help="persona source Markdown path")
    parser.add_argument("--runtime", required=True, help="OrbitOS runtime root")
    parser.add_argument("--confirm-baseline", action="store_true")
    parser.add_argument("--identity", help="replace the stable identity line")
    parser.add_argument("--accept-suggestion", help="suggestion id to accept")
    parser.add_argument("--dismiss-suggestion", help="suggestion id to dismiss")
    parser.add_argument("--confirmed-id", help="id for the confirmed pattern created from an accepted suggestion")
    parser.add_argument("--confirmed-statement", help="user-confirmed pattern statement")
    parser.add_argument("--evidence", help="evidence for the confirmed pattern")
    parser.add_argument("--note", help="optional handling note attached to the suggestion")
    parser.add_argument("--no-refresh-collab", action="store_true", help="skip refreshing the collaboration projection")
    args = parser.parse_args()

    actions = apply_update(
        Path(args.source),
        Path(args.runtime),
        confirm_baseline=args.confirm_baseline,
        identity=args.identity,
        accept_suggestion=args.accept_suggestion,
        dismiss_suggestion=args.dismiss_suggestion,
        confirmed_id=args.confirmed_id,
        confirmed_statement=args.confirmed_statement,
        evidence=args.evidence,
        note=args.note,
        refresh_collab=not args.no_refresh_collab,
    )
    print("persona update applied: " + ", ".join(actions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
