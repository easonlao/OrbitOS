# OrbitOS Modules

Modules are optional capabilities. Agents load a module only when its trigger is present; missing or unused modules must not block core inbox, knowledge, project, status, or validation work.

- `collaboration/`: cross-agent handoff after delegated work.
- `persona/`: explicit persona baseline, calibration, and confirmed updates.
- `hindsight/`: optional cross-session memory recall and retain bridge.
- `thinking/`: on-demand thinking-method recommendations.
- `engineering/`: optional code-project integration with Matt Pocock Skills after explicit user enablement.
- `automation/`: user-confirmed external scheduled checks and task catalog.
- `reading/`: Agent-neutral reading import, deep-reading, annotation, and source-traceability capabilities.

Core runtime behavior stays in `.orbitos/rules/core/`, `.orbitos/workflows/`, `.orbitos/schemas/`, `.orbitos/scripts/`, and `.orbitos/templates/`.
