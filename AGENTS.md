# AGENTS.md — Coding-KI Arbeitsvertrag (verbindlich)

Dieses Dokument definiert **WIE** eine Coding-KI an diesem Projekt arbeitet.
Es ist **kein** Produktspezifikationsdokument.

Bei Widersprüchen gilt immer:
1. UNIFIED.md
2. TICKETS.md
3. AGENTS.md

---

## 1. Grundprinzipien
- Keine Annahmen treffen.
- Wenn etwas unklar ist: **STOP** und rückfragen.
- Keine Optimierungen, kein Refactoring ohne explizites Ticket.
- Erst minimal, dann integrieren.
- Fehler sind Signale, kein Anlass für Workarounds.

---

## 2. Arbeitsmodus
- Tickets streng sequentiell abarbeiten.
- Jedes Ticket vollständig abschließen (DoD erfüllt).
- Kein Vorausarbeiten.
- Kein Überspringen von Phasen.

---

## 3. UI- und Threading-Disziplin
- UI-Thread fasst Widgets an, sonst niemand.
- Background-Threads erzeugen nur Events.
- Keine direkten Widget-Referenzen speichern.
- `refresh()` ist **kein** Problemlöser.
- Alles TCSS in eine zentrale .tcss-Datei.

Bei UI-Problemen:
1. Minimalbeispiel (Kata)
2. Verhalten verstehen
3. Erst dann Integration

---

## 4. Änderungsregeln
Änderungen an States, UX, Keybindings oder Threading nur mit Ticket oder Freigabe.

---

## 5. Abbruchkriterien
Arbeit abbrechen, wenn:
- State-Maschine umgangen werden soll
- UI per Workaround „repariert“ wird
- `refresh()` inflationär nötig scheint
- mehrere STT-Worker parallel laufen sollen

---

## 6. Ziel
Robust, reproduzierbar, praxisgeeignet – nicht „irgendwie lauffähig“.


## 🧪 Textual UI Debugging – **Mandatory Procedure**

This project uses **Textual** for TUI development.  
**UI / UX issues MUST be debugged using Textual devtools. Guessing is not acceptable.**

---

### 1. Required Devtools
For any Textual UI bug, you MUST use:

- `textual console` (log output, diagnostics)
- `textual run --dev <entrypoint>` (development mode with live TCSS reload)

Do NOT propose layout or style changes without evidence from devtools.

---

### 2. Mandatory Debug Questions (in this order)
For every UI issue, explicitly answer the following:

1. **Is the widget mounted and present in the widget tree?**  
   Identify by `id`, `classes`, and full widget path.
2. **Is the widget visible?**  
   Check visibility / display state.
3. **What are the widget’s layout bounds after layout?**  
   Provide x / y / width / height.
4. **Is the widget clipped or outside the viewport?**  
   Inspect parent containers, scrolling, docking.
5. **Which TCSS rules apply to this widget?**  
   Identify selectors by `#id` / `.class`.

If any of these cannot be answered, request the missing devtools output instead of guessing.

---

### 3. Evidence Requirements
Any proposed fix MUST reference at least one of the following:

- Widget tree evidence (path, id, classes)
- Layout bounds (zero-size, off-screen, clipped)
- Relevant TCSS selectors (by id or class)
- Devtools console output

**Required justification style:**
> “Widget `#submit` exists in tree, but computed width is 0 due to parent grid constraints.  
> Fix adjusts grid column definition.”

---

### 4. Prohibited Behavior
- ❌ Blind TCSS tweaks without identifying the affected widget
- ❌ Layout changes without confirming widget bounds
- ❌ Speculative language (“probably”, “might be”, “try increasing height”)
- ❌ Debugging based only on visual description

If evidence is missing, the correct action is to **request devtools output**, not to speculate.

---

### 5. Preferred Workflow
1. Run `textual console`
2. Run app via `textual run --dev`
3. Reproduce the issue
4. Inspect widget tree / layout / TCSS
5. Propose **minimal, evidence-backed fix**
6. Re-run and verify

---

### 6. Goal
Textual UI debugging must follow the same rigor as web debugging with DOM + CSS DevTools.

**Evidence first. Changes second.**

