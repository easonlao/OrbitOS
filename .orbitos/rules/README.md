# OrbitOS Rules

This directory contains rules that agents must follow while operating OrbitOS.

## Layers

- `core/`: stable rules that are active by default.
- Runtime does not maintain learned-rule state or a self-evolving rule workflow.

## Boundary

Rules are executable constraints for agents.

Design notes, rationale, alternatives, and planning belong in the project development layer managed outside Product Repo, not in `.orbitos/`.

Rules change only through explicit product updates and validation.
