# STT-Diktat-Agent

Lokaler **Speech-to-Text-Diktat-Agent** für eine Hausarztpraxis auf Windows 11.  
Die Ärztin diktiert (kein Dialog), erhält **sofortiges Live-Feedback** (Pegel, Warnungen, Early Snippet nach ~8 s) und am Ende ein vollständiges Transkript.

---

## Features

- **Fail-Fast:** Live-Pegel und Audio-Warnungen (stumm, zu leise, Clipping) binnen ≤2 s
- **Early Snippet:** Nach 8 s (konfigurierbar) eine STT-Vorschau mit Ampel (🟢/🟡/🔴) zur frühen Qualitätsentscheidung
- **Fokus-TUI:** Eine übersichtliche Textual-Ansicht mit klarem Status (READY, REC, PAUSE, PROCESSING, DONE, ERROR)
- **Better-Model Redo (F8):** Transkript mit besserem Modell neu erzeugen, ohne erneute Aufnahme
- **Lokaler STT:** `faster-whisper` (CPU-only), keine Cloud-Übertragung; Modell-Download nur beim ersten Start
- **State-driven UI:** Saubere Trennung von UI-Thread und Worker-Threads; Kommunikation nur über Events

---

## Voraussetzungen

- **Windows 11**
- **Python ≥ 3.11**
- Mikrofon (idealerweise Headset)  
- Keine GPU nötig (CPU-only)

---

## Installation

### 1. Repository klonen

```bash
git clone <repository-url>
cd stt_better
```

### 2. Virtual Environment und Abhängigkeiten

**PowerShell (empfohlen):**

```powershell
.\scripts\install.ps1
```

Das Skript prüft Python, erstellt `.venv` und installiert aus `requirements.lock.txt` (u.a. textual, sounddevice, faster-whisper, numpy).

Venv neu aufsetzen:

```powershell
.\scripts\install.ps1 -Force
```

**Manuell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock.txt
```

### 3. Konfiguration (optional)

Die Datei `config.toml` im Projektroot steuert Audio, Snippet und STT. Beispiele:

| Sektion     | Option              | Bedeutung                         | Default   |
|------------|---------------------|-----------------------------------|-----------|
| `[audio]`  | `device`            | Mikrofon (Name/Index, leer = Default) | `""`      |
| `[audio]`  | `samplerate`        | Abtastrate                        | `16000`   |
| `[audio]`  | `channels`          | Kanäle                            | `1`       |
| `[snippet]`| `seconds`           | Sekunden bis Early Snippet        | `8`       |
| `[stt]`    | `model`             | Modell (tiny, base, small, medium)| `small`   |
| `[stt]`    | `compute_type`      | z.B. `int8`                       | `int8`    |
| `[stt]`    | `language`          | Sprache                           | `de`      |
| `[retention]` | `recordings_days` | Aufbewahrung Aufnahmen (Tage)     | `7`       |
| `[retention]` | `logs_days`       | Aufbewahrung Logs (Tage)          | `14`      |

---

## Start

Mit aktiviertem venv:

```powershell
.\.venv\Scripts\Activate.ps1
python -m app.main
```

Oder über das Modul:

```powershell
python -m app.main
```

**Entwicklungsmodus (Textual, live TCSS-Reload):**

```powershell
textual run --dev app.main
```

**Textual Console (Logs/Diagnostik):**

```powershell
textual console
# in anderem Terminal: textual run --dev app.main
```

---

## Tastaturkürzel

| Taste | Aktion |
|-------|--------|
| **F9**  | Aufnahme starten / pausieren / fortsetzen; in DONE: neues Diktat |
| **F10** | Aufnahme stoppen (WAV finalisieren, Full-STT starten) |
| **F6**  | Transkript in die Zwischenablage kopieren (nur in DONE) |
| **F8**  | Redo mit besserem Modell (nur in DONE, wenn Upgrade möglich) |
| **F2**  | Doctor / Preflight (Mic, Modell, Konfiguration) |
| **Esc** | Beenden (mit Bestätigung bei laufender Aufnahme/Verarbeitung) |

---

## Projektstruktur (Kurz)

| Ordner     | Inhalt |
|-----------|--------|
| `app/`    | Orchestrierung, State Machine, Job-Lifecycle, Events |
| `ui/`     | Textual Fokus-TUI, Widgets, Layout, `app.tcss` |
| `services/` | Audio-Capture, STT (faster-whisper), Doctor, Recording, Snippet-Tracker |
| `domain/` | States, Enums, Dataclasses |
| `util/`   | Config, Logging, Pfade |
| `scripts/`| `install.ps1`, Doctor/Preflight, evtl. Benchmarks |
| `data/`   | Laufzeitdaten (recordings, transcripts, db, logs, cache) – gitignored |

Detaillierte Regeln und Import-Richtungen: **STRUCTURE.md**.

---

## Technologie-Stack

- **UI:** [Textual](https://textual.textualize.io/) (TUI)
- **Audio:** `sounddevice`, WAV 16 kHz mono
- **STT:** `faster-whisper` (CTranslate2), CPU-only
- **Deployment:** Python venv, `requirements.lock.txt`, kein Docker
- **Parallelität:** genau 1 Full-STT-Worker (seriell)

---

## Dokumentation (Referenz)

| Dokument     | Zweck |
|-------------|--------|
| **UNIFIED.md**   | Konsolidierte Spezifikation (Ziel, Architektur, States, Keybindings, Services, Pfade, Konfiguration) |
| **STRUCTURE.md** | Verbindliche Projektstruktur, Ordnerverantwortlichkeiten, Import- und Thread-Regeln |
| **UX_TUI.md**    | Layout und UX der Fokus-TUI (ASCII, Bereiche, Keybindings, Flows) |
| **AGENTS.md**    | Arbeitsregeln für Coding-KIs (Threading, UI, Änderungen, Textual-Debugging) |
| **TICKETS.md**   | Sequenzielle Arbeitsreihenfolge, DoD, aktueller Stand |

Bei Konflikten: **UNIFIED.md** > TICKETS.md > AGENTS.md.

---

## Entwicklung

- **Tests:** `tests/` (Unit: Audio-Qualität, STT-Qualität; Integration: Doctor, Bench mit Fixture-Audio)
- **Playground:** `playground/` für Textual-Katas und Experimente; Code nicht direkt ins Produkt übernehmen
- **TCSS:** zentral in `ui/app.tcss`
- **UI-Debugging:** Siehe AGENTS.md — `textual run --dev`, `textual console`, Widget-Tree und TCSS-Referenz vor Änderungen nutzen

---

## Daten und Datenschutz

- **Pfade:** `data/recordings/`, `data/transcripts/`, `data/db/`, `data/logs/`, `data/cache/`
- Keine Audio- oder Textinhalte in Logs; nur Job-ID, Status, Laufzeiten, Fehlercodes
- `data/` ist in `.gitignore`

---

## Status

Projekt in Entwicklung. Aktueller Stand und offene Punkte: **TICKETS.md**.

---

## Lizenz

(Bei Bedarf ergänzen.)
