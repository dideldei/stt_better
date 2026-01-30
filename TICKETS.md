# TICKETS.md — STT-Diktat-Agent  
## Fokus-TUI · zustandsgetrieben · KI-robust

Diese Tickets sind **explizit für eine Coding-KI** formuliert.
Sie berücksichtigen typische Fehlermuster (Textual-UI, Threading, State-Sync)
und erzwingen **inkrementelles, überprüfbares Vorgehen**.

Es gibt **keine Verbose-Ansicht** mehr.  
Die Fokus-TUI (`UX_TUI.md`) ist die **einzige produktive UI**.

---

## VERBINDLICHER RAHMEN

- Plattform: Windows 11
- Sprache: Python
- UI: Textual
- Ansicht: **nur Fokus-TUI**
- Kein Docker, kein Web, keine GUI
- STT: CPU-only, **1 Full-STT-Worker (seriell)**
- UI-Updates ausschließlich im UI-Thread
- `widget.update()` ist Standard  
  `refresh()` nur bei Custom-Widgets mit Begründung
- Erst Pattern beherrschen → dann integrieren

---

# PHASE 0 — TEXTUAL-PATTERN ABSICHERN (PFLICHT)

## 0.1 Textual Update Kata (isoliert)
**Ziel:** Die KI beweist Textual-Grundverständnis, unabhängig vom Projekt.

**Aufgabe:**
- `playground/textual_update_kata/kata_app.py`
- Minimal-UI:
  - Header (Status)
  - Log-Area
- Keybindings:
  - F1 → Status ändern (UI-Thread)
  - F2 → Background-Task erzeugt 10 Events (1/s)
  - Esc → Quit

**DoD (prüfbar):**
- F1 ändert sichtbaren Text sofort
- F2 zeigt 10 Updates live
- Keine `refresh()`-Aufrufe im Code
- Logs zeigen:
  - Background-Thread ≠ UI-Thread
  - UI-Updates im UI-Thread

➡️ **STOP** – erst weiter, wenn erfüllt.

---

# PHASE 1 — PROJEKTGERÜST (NOCH OHNE DYNAMIK)

## 1.1 Struktur & Start
**DoD:**
- Ordner existieren: `app/ ui/ services/ domain/ util/`
- App startet & beendet sich sauber
- Fokus-TUI leer sichtbar
- Kein Threading, kein Audio, kein STT

## 1.2 Config & Logging
**DoD:**
- `config.toml` wird geladen
- Fehlerhafte Config → sauberer Exit
- Logfile existiert
- Keine PHI im Log

---

# PHASE 2 — FOKUS-TUI STATISCH

## 2.1 Layout gemäß UX_TUI.md
**DoD:**
- ASCII-Layout 1:1 umgesetzt
- Alle Widgets haben **eindeutige IDs**
- Keine Event-Handler
- Keine dynamischen Updates

---

# PHASE 3 — ZUSTANDSMASCHINE (OHNE THREADS)

## 3.1 States & Events
**Ziel:** UI und Logik strikt trennen.

**Aufgabe:**
- States gemäß `STATE_MACHINE.md`:
  READY · RECORDING · PAUSED · PROCESSING · DONE · ERROR
- Event-Typen (UI + Service)

**DoD:**
- Ungültige Transitionen werden blockiert
- Jeder State-Wechsel wird geloggt
- Noch keine Threads



## 3.2 Reactive State-Bindung
**Ziel:** UI reagiert ausschließlich auf State.

**DoD:**
- Reactive Felder gemäß `UI_BINDINGS`
- State-Wechsel → sichtbare UI-Änderung
- Kein direkter Widget-Zugriff aus Logik
- Kein `refresh()`

# PHASE 3.5 — DOCTOR / PREFLIGHT (MVP, verbindlich)

## 3.5.1 Doctor-Checks (ohne Audioaufnahme, ohne STT)
**Ziel:** F2 (Doctor) ist real implementiert und die App startet sauber in INIT und landet in READY/ERROR.

**Checks (Minimum):**
- Pfad-Schreibtest in `data/` (recordings/, transcripts/, db/, logs/, cache/)
- `requirements.lock.txt` vorhanden (nur Info, kein Install)
- STT-Modell **nur prüfen, ob ladbar** (kein Download erzwingen)
- Mikrofon-Geräteliste nur anzeigen/prüfen (kein Stream öffnen)

**DoD (prüfbar):**
- App startet in INIT, zeigt „DOCTOR…“ im Header
- Bei Erfolg: State wird READY, Header zeigt „READY ✅“, Mic/Model OK
- Bei Fehler: State wird ERROR mit `error_code` + `hint` (PHI-frei)
- F2 triggert Doctor nur in READY/DONE/ERROR (in RECORDING/PAUSED/PROCESSING: No-Op + Hinweis)
- Doctor blockiert UI nicht (läuft async, Events zurück)

## 3.5.2 doctor.ps1 Script (optional aber empfohlen)
**Ziel:** Ein CLI-Check für Admin/Setup unabhängig von der UI.

**DoD (prüfbar):**
- `scripts/doctor.ps1` läuft ohne venv-Aktivierung (nutzt .venv absolute Pfade)
- gibt am Ende klar „OK“ oder „FAIL“ zurück (ExitCode 0/1)
- schreibt nichts in Log außer Pfad/Status (keine PHI)


---

# PHASE 4 — KEYBINDINGS (STATE-GATED)

## 4.1 Tastenlogik
**DoD:**
- F9 in READY / RECORDING / PAUSED **und DONE** (DONE → neues Diktat starten, Transkript UI leeren)
- F10 nur in RECORDING / PAUSED
- F6 & F8 nur in DONE
- F2 (Doctor) nur in READY / DONE / ERROR (in RECORDING/PAUSED/PROCESSING: No-Op + Hinweis)
- Ungültige Eingaben → No-Op + Log

---

# PHASE 5 — THREADING (NOCH OHNE AUDIO / STT)

## 5.1 Background → UI Events
**Ziel:** Thread-sichere Kommunikation.

**DoD:**
- Background-Thread erzeugt Fake-Events
- UI verarbeitet Events im UI-Thread
- Logs zeigen klar Thread-Trennung
- Keine Widget-Updates aus Threads

## 5.2 Widget-Instanzen absichern
**DoD:**
- Updates nur über reactive/watch oder `query_one("#id")`
- `widget.is_mounted == True` im Log
- Keine gespeicherten Widget-Referenzen

---

# PHASE 6 — AUDIO (FAKE)

## 6.1 Fake-Audio-Service
**DoD:**
- Pegel bewegt sich sichtbar
- Update-Rate ≤ 10 Hz
- Kein Flackern

---

# PHASE 7 — EARLY SNIPPET (FAIL-FAST)

## 7.1 Fake-Snippet-Flow
**DoD:**
- Snippet erscheint nach ~8 s **kumulativer Aufnahmezeit** (Pause zählt nicht)
- Ampel 🟢🟡🔴 sichtbar
- Aufnahme läuft weiter

**Status:** ✅ Teilweise erfüllt
- ✅ Snippet erscheint korrekt nach 8s (logs bestätigen: threshold reached, snippet generated)
- ✅ Aufnahme läuft weiter (keine State-Änderung bei Snippet)
- ⚠️ Ampel-Widget wird aktualisiert (logs zeigen `widget.update("🟢 Qualität: Gut")` erfolgreich), aber **nicht sichtbar im TUI**

**Workaround (temporary):**
Snippet-Text und Qualität werden kombiniert dargestellt: `"{snippet_text}\n\n{quality}"` in einem Widget.

## 7.2 Textual Layout-Fix für Snippet-Qualität
**Ziel:** Qualitäts-Ampel (🟢🟡🔴) korrekt im TUI anzeigen.

**Problem:**
- `snippet_quality` Widget wird per `widget.update()` korrekt aktualisiert (logs bestätigen)
- Widget ist `is_mounted=True, visible=True, display=True` (logs bestätigen)
- Aber Widget-Inhalt erscheint **nicht** im gerenderten TUI

**Hypothesen (aus Debug-Session):**
- A) ✅ Separator-Zeile zu lang → gekürzt von 47 auf 37 Zeichen (fixed)
- B) ✅ Container-Höhe zu klein → erhöht von 8 auf 10 (fixed)
- C) ✅ widget.update() funktioniert (logs beweisen es)
- D) ⚠️ Textual Static-Widget mit leerem Initial-Content wird nicht gerendert
- E) ⚠️ Reactive-Update triggert kein Layout-Recalc in Textual
- F) ⚠️ Textual-Rendering-Pipeline ignoriert dynamische Updates

**Nächste Schritte:**
1. Textual Docs/Beispiele zu dynamischen Static-Widget-Updates prüfen
2. Alternative Widgets testen (Label statt Static)
3. Explizites `refresh()` nur für diesen Fall prüfen (mit Begründung)
4. Community-Patterns für ähnliche Use-Cases recherchieren

**DoD:**
- Ampel 🟢🟡🔴 erscheint visuell im TUI unter "EARLY SNIPPET"
- Separate Widget-Darstellung (kein kombinierter Text-Workaround)
- Kein `refresh()` ohne zwingende Begründung
- Pattern dokumentiert für zukünftige dynamische Updates

---

# PHASE 8 — STT (ECHT)

## 8.1 faster-whisper Setup
**DoD:**
- Modell lädt beim Start
- Warmup läuft
- CPU-only

## 8.2 Snippet-STT (real)
**DoD:**
- Snippet-Transkript während Aufnahme
- delayed: Fehler → Ampel rot + Hinweis
- UI blockiert nicht

## 8.3 Full-STT (seriell)
**DoD:**
- Genau **1** Worker
- PROCESSING → DONE / ERROR korrekt
- F6/F8 erst in DONE aktiv

---

# PHASE 9 — PERSISTENZ

## 9.1 SQLite Job-Index
**DoD:**
- Status & Pfade persistiert
- Crash → konsistenter Restart

---

# PHASE 10 — END-TO-END

## 10.1 Smoke-Test
**DoD:**
- READY → RECORDING → PROCESSING → DONE
- Early Snippet sichtbar
- Copy (F6) funktioniert
- Redo (F8) funktioniert
- App bleibt responsiv

---

## ABSOLUTES STOP-KRITERIUM

Wenn ein Ticket:
- `refresh()` inflationär nutzt
- Threads direkt Widgets anfassen
- die Zustandsmaschine umgeht

➡️ **Ticket abbrechen und zum vorherigen zurückkehren.**

---

**Diese Tickets sind verbindlich.  
Optimierungen sind NICHT erlaubt.**
