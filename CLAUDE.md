# CLAUDE.md — pem-ec-designer (Projekt 2, Placeholder)

**Status:** Leeres Skelett. Projekt-Arbeit beginnt in einer **neuen Session**.

---

## Vor dem ersten Commit — Pflichtlektüre

1. **`../docs/simulation-project-framework.md`** — die 8 Pflichtfragen durcharbeiten
   und als `docs/adr/001-framework-choice.md` beantworten.
2. **`../docs/lessons/pem-ec-0d.md`** — 5 dokumentierte Strukturfehler aus dem
   Vorgänger-Projekt. Mindestens einmal lesen, damit sie sich hier nicht
   wiederholen.

## Scope-Hinweis (vorläufig, bis ADR-001 geschrieben ist)

Nachfolger von `pem-ec-0d`. Ziel: echter **visueller Designer** mit
3D/CAD-Darstellung und Stack-Konstruktion. Framework-Empfehlung aus Lessons:
**NiceGUI** oder **Panel + pyvista**, nicht Streamlit (siehe Lesson #1).

Physik-Wiederverwendung aus `pem-ec-0d/src/` ist erlaubt und erwünscht —
Strategie (Submodule / Package / Copy) in ADR-002 entscheiden.

## Keine Scaffolds ohne ADR-001

Kein `requirements.txt`, kein `src/`, kein `pyproject.toml`, bevor die
8 Pflichtfragen beantwortet sind. Das war der Kardinalfehler in pem-ec-0d.

## Session-Start

```bash
cd /Users/abed.qadi/projects/Simulation-tools/pem-ec-designer
claude
# Erste Aufgabe: Pflichtfragen aus simulation-project-framework.md beantworten,
# Framework-ADR schreiben, dann erst scaffolden.
```
