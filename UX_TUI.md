# UX_TUI.md — Fokus-TUI (Iteration 2, verbindlich)

Diese Datei beschreibt die **einzige und verbindliche TUI** des STT-Diktat-Agenten.
Es gibt **keine separate Verbose- oder Advanced-Ansicht** mehr.

Die Fokus-TUI ist:
- Default beim Start
- einzige produktive Ansicht
- optimiert für den Praxisalltag

Bei Konflikten gilt folgende Priorität:
1. SPEC.md
2. ARCHITECTURE.md
3. UX_TUI.md
4. TICKETS.md

---

## 1. Fokus-Layout (ASCII, verbindlich)

```text
┌───────────────────────────────────────────────────────────────┐
│ STT-Diktat-Agent | READY ✅ | Mic: OK | Model: OK              │
│ F9 Rec/Pause/Resume | F10 Stop | F6 Copy | Esc Quit | F2 Doctor│
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│ STATUS                                                       │
│ ─────────────────────────────────────────────────────────── │
│ Aufnahme: AUS | Transkript: —                                │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────┐ ┌─────────────────────────────────────┐
│ LIVE FEEDBACK         │ │ EARLY SNIPPET                        │
│ ───────────────────── │ │ ─────────────────────────────────── │
│ Pegel: [■■■■■■□□□□]   │ │ (leer / Vorschau / Hinweis)          │
│ Warnungen: (keine)    │ │                                     │
└───────────────────────┘ └─────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│ TRANSKRIPT                                                   │
│ ─────────────────────────────────────────────────────────── │
│ (noch nicht verfügbar)                                       │
│                                                             │
│                                                             │
│ ────────────────────────────────────────────────────────── │
│ F8 Redo with better model | F6 Copy                          │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. Bedeutung der Bereiche

### 2.1 Header
**Zweck:** Sofortige Betriebssicherheit

Zeigt immer:
- globalen Status (READY / REC / PAUSE / PROCESSING / DONE)
- Mikrofonstatus
- Modellstatus

**Regeln:**
- Header aktualisiert sich sofort bei Zustandswechsel
- Keine Detailinformationen
- Keine Scrolls

---

### 2.2 STATUS
**Zweck:** Eine Zeile = zwei Kernfragen

```text
Aufnahme: AUS | Transkript: —
```

**Aufnahme**
- AUS
- ● LÄUFT
- ⏸ PAUSE
- ⏹ GESTOPPT

**Transkript**
- —
- ⏳ wird erstellt
- ✅ fertig
- ❌ Fehler

Diese Zeile ist **führend** und muss immer korrekt sein.

---

### 2.3 LIVE FEEDBACK
**Zweck:** Fail-Fast während der Aufnahme

Inhalt:
- Pegel (visuell)
- Warnungen:
  - kein Signal
  - zu leise
  - Clipping

**Regeln:**
- Update-Rate ≤ 10 Hz
- Keine Zahlenpflicht
- Warnung ersetzt „(keine)“

---

### 2.4 EARLY SNIPPET
**Zweck:** Frühe Qualitätsentscheidung

Zustände:
- leer (Snippet noch nicht geprüft)
- Vorschau-Text (1–2 Zeilen)
- Hinweistext (z. B. „kein Sprachsignal erkannt“)

**Regeln:**
- Snippet erscheint automatisch (~8 s)
- Snippet wird **während laufender Aufnahme** angezeigt
- Keine Interaktion in diesem Bereich

---

### 2.5 TRANSKRIPT
**Zweck:** Ergebnis + Folgeaktionen

Zustände:
- leer
- ⏳ wird erstellt
- vollständig (scrollbar)

Footer-Aktionen:
- **F6 Copy** → kopiert aktuellen Text
- **F8 Redo with better model** → erneute STT-Ausführung ohne Neuaufnahme

---

## 3. Keybindings (verbindlich)

| Taste | Aktion |
|-----|-------|
| F9 | Aufnahme starten / pausieren / fortsetzen |
| F10 | Aufnahme stoppen |
| F6 | Transkript kopieren |
| F8 | Redo mit besserem Modell |
| F2 | Doctor / Preflight |
| Esc | Beenden (mit Bestätigung bei aktivem Job) |

---

## 4. UX-Flows

### 4.1 Standardfluss
1. READY
2. F9 → ● LÄUFT
3. Live-Feedback aktiv
4. Early Snippet erscheint
5. F10 → Stop
6. Transkript ⏳ → ✅
7. F6 Copy

---

### 4.2 Pause / Resume
- F9 während Aufnahme → ⏸ PAUSE
- Pegel stoppt
- F9 erneut → ● LÄUFT
- Snippet-Timer läuft weiter

---

### 4.3 Schlechte Qualität
- Warnungen im Live-Feedback
- Snippet leer/unplausibel
- Nutzer entscheidet selbst:
  - weiter diktieren
  - stoppen
  - neu starten

---

### 4.4 Redo mit besserem Modell
- Nur möglich bei fertigem Transkript
- Audio wird wiederverwendet
- UI zeigt klaren Re-Processing-Zustand

---

## 5. Design-Prinzipien (nicht verhandelbar)

- Fokus-TUI ist die **einzige Ansicht**
- Keine Popups während Aufnahme
- Keine versteckten Zustände
- Jede Aktion führt zu sichtbarem Feedback
- Kein automatisches Umschalten in andere Views

---

**Dieses Dokument ist verbindlich und maßgeblich für die Implementierung durch eine Coding-KI.**
