# UNIFIED.md — STT-Diktat-Agent (Single Arbeitsplatz, Fokus-TUI, konsolidiert)

Dieses Dokument ist die **konsolidierte, konfliktfreie Referenz** für das Projekt.


Wenn andere Dokumente abweichen, gilt ab jetzt:
1) **UNIFIED.md**
2) TICKETS.md (nur Arbeitsreihenfolge, nicht Spezifikation)

---

## 1. Ziel, Scope, Nicht-Ziele

### 1.1 Ziel
Lokaler STT-Diktat-Agent für eine Hausarztpraxis auf **Windows 11**:  
Ärztin diktiert (kein Dialog), und erhält **zuverlässiges, sofortiges Feedback**, ob Aufnahme/STT funktionieren. fileciteturn1file4

### 1.2 Kern-Anspruch: Fail-Fast
Fehler müssen **während** des Diktats sichtbar werden, nicht erst am Ende:
- Live-Pegel + Audio-Warnungen binnen ≤2s
- **Early Snippet** nach **8s** (konfigurierbar, Default 8) mit Vorschau + Ampel file3turn1file8turn1file2

### 1.3 Nicht-Ziele (MVP)
- Keine Dialog-/Mehrsprecher-Erkennung
- Keine Cloud-Übertragung (außer initialer Modell-Download)
- Keine direkte PVS-Integration
- Keine medizinische Entscheidungsunterstützung fileciteturn1file4

---

## 2. Verbindliche Technologie-Entscheidungen

- **UI:** Textual TUI (eine einzige Fokus-Ansicht), Reference use regularily: https://textual.textualize.io/reference/

- **Audio:** `sounddevice`, WAV 16kHz mono   
- **STT:** `faster-whisper` (CTranslate2), CPU-only fileciteturn1file4turn1file3  
- **Deployment:** Python venv, pinned deps, kein Docker fileciteturn1file4turn1file3  
- **Parallelität:** exakt **1 Full-STT-Worker (seriell)** fileciteturn1file4turn1file3turn1file2  

---

## 3. Architektur-Grundprinzipien (nicht verhandelbar)

### 3.1 State-driven UI
> Event → State Change → Render (UI reagiert auf Zustand, nicht auf direkte Aufrufe) fileciteturn1file0turn1file3

### 3.2 Threading-Regeln
- UI-Thread blockiert nie und macht keine I/O/STT. fileciteturn1file0turn1file3  
- Worker/Callback-Threads fassen **keine Widgets** an. fileciteturn1file0turn1file3  
- Kommunikation ausschließlich über Events/Queue/Messages. fileciteturn1file0turn1file2turn1file7  
- `refresh()` ist **kein Fix**. fileciteturn1file0turn1file7  

---

## 4. Fokus-TUI (einzige Ansicht)

### 4.1 Layout (verbindlich)
Siehe UX_TUI.md-ASCII (identisch). fileciteturn1file8

### 4.2 Keybindings (verbindlich, konsolidiert)
**Es gibt KEIN F7 mehr.** (Save Transcript ist gestrichen; Persistenz erfolgt automatisch.) fileciteturn1file1

| Taste | Aktion | Erlaubt in States |
|---|---|---|
| F9 | Rec / Pause / Resume; in DONE: **neues Diktat starten** (Job reset) | READY, RECORDING, PAUSED, DONE |
| F10 | Stop (finalize WAV, start Full-STT) | RECORDING, PAUSED |
| F6 | Copy Transcript (Clipboard) | DONE |
| F8 | Redo with better model (ohne Neuaufnahme) | DONE (nur wenn noch upgrade möglich) |
| F2 | Doctor / Preflight | READY, DONE, ERROR |
| Esc | Quit (mit Confirm bei laufender Arbeit) | immer |

Hinweise:
- In PROCESSING ist F9/F10/F2 deaktiviert (No-Op + Hinweis).
- In ERROR ist F6/F8 deaktiviert (Default: kein Copy/Redo bei Fehler). fileciteturn1file5

### 4.3 Statusanzeige (Header/Statusline)
- Header zeigt: State + Mic + Model (OK/FAIL/UP) fileciteturn1file8turn1file7
- STATUS-Zeile ist **führend** (Aufnahme / Transkript). fileciteturn1file8

---

## 5. Zustandsmaschine (UI-State, verbindlich)

### 5.1 Zustände
Wir nutzen ein **UI-fokussiertes Modell**:
- INIT (nur Startphase/Doctor)
- READY
- RECORDING
- PAUSED
- PROCESSING
- DONE
- ERROR fileciteturn1file5turn1file1

### 5.2 Startsequenz
1) App startet in **INIT**
2) Auto-Doctor/Preflight läuft
3) Ergebnis:
   - OK → READY
   - FAIL → ERROR (mit code + hint) fileciteturn1file4turn1file5

### 5.3 Transitionen (konsolidiert)
- READY --F9--> RECORDING
- RECORDING --F9--> PAUSED
- PAUSED --F9--> RECORDING
- RECORDING/PAUSED --F10--> PROCESSING
- PROCESSING --FullSTT_Done--> DONE
- PROCESSING --FullSTT_Fail--> ERROR
- DONE --F8--> PROCESSING (Redo)
- DONE --F9--> RECORDING (Start new dictation; clears transcript UI + resets snippet state)
- READY/DONE/ERROR --F2--> INIT (Doctor) -> READY/ERROR
- Esc: Confirm bei RECORDING/PAUSED/PROCESSING; sofort bei READY/DONE/ERROR fileciteturn1file5turn1file1

### 5.4 Invarianten
- Max 1 Full-STT gleichzeitig (seriell).
- UI-Thread rule strikt.
- Live-Meter ≤10 Hz.
- Snippet-Trigger basiert auf **kumulativer Recording-Zeit**, Pause zählt nicht. fileciteturn1file5turn1file8turn1file1

---

## 6. UI-Bindings (reactive, verbindlich)

### 6.1 Update-Pattern
- Background erzeugt Events
- UI konsumiert Events (Timer/Message handler)
- UI setzt reactive Felder
- Widgets rendern aus reactive Feldern fileciteturn1file7turn1file0

### 6.2 Reactive Felder (Minimal)
- `app_state`, `header_mic`, `header_model`, `rec_timer`
- `status_recording`, `status_transcript`
- `level_bar`, `warnings`
- `snippet_text`, `snippet_quality`
- `transcript_text`
- optional: `last_error_code`, `last_error_hint` fileciteturn1file7

### 6.3 Widget-IDs (Minimal, verbindlich)
- `#hdr_state`, `#hdr_mic`, `#hdr_model`
- `#status_line`
- `#level_bar`, `#warnings`
- `#snippet_text`, `#snippet_quality`
- `#transcript_box`, `#footer_actions` fileciteturn1file7turn1file8

---

## 7. Services & Verantwortlichkeiten (konsolidiert)

### 7.1 Orchestrator
- zentrale State Machine + Job-Lifecycle
- steuert Services
- serialisiert Full-STT (1 Worker)
- mappt Errors auf ERROR + code/hint fileciteturn1file2turn1file0

### 7.2 Audio Capture (`sounddevice`)
- Stream/Callback in eigenem Thread
- Callback darf nur puffern + RMS/Peak berechnen
- WAV-Schreiben außerhalb Callback
- LevelUpdated Events throttled (≤10 Hz)
- Snippet-WAV nach `snippet.seconds` (Default 8) fileciteturn1file2turn1file3

### 7.3 Qualitätsanalyse (Audio)
- stumm/zu leise/clipping
- Warnungen in LIVE FEEDBACK

### 7.4 STT Engine (`faster-whisper`)
Defaults (verbindlich):
- model: `small`
- compute_type: `int8`
- beam_size: `5`
- language: `de` fileciteturn1file3turn1file2turn1file4

Warmup:
- Model load + warmup beim Start (Doctor)
- Keine Downloads während RECORDING/PAUSED/PROCESSING fileciteturn1file3turn1file4

### 7.5 STT-Qualität (Snippet-Ampel)
- nutzt faster-whisper Metriken (no_speech_prob, avg_logprob, compression_ratio)
- Ergebnis: 🟢/🟡/🔴 + kurze Empfehlung fileciteturn1file4turn1file2

---

## 8. Better-Model Redo (F8) — exakt definiert

### 8.1 Upgrade-Kette (fest)
`tiny` → `base` → `small` → `medium` (Maximum) fileciteturn1file5turn1file1

### 8.2 Verhalten
- F8 nur in DONE.
- Wenn aktuelles Modell bereits `medium`: F8 ist disabled.
- Während Upgrade/Laden:
  - Header „Model: UP“
  - nach Erfolg: „Model: OK“
- Redo überschreibt **das sichtbare** Transkript (kein Versions-UI im MVP).
- Download falls nötig ist erlaubt **nur** in DONE/READY/ERROR (nie während Aufnahme/Processing). fileciteturn1file7turn1file5turn1file3

---

## 9. Datenhaltung, Pfade, Datenschutz

### 9.1 Pfade (verbindlich)
- `data/recordings/<jobid>.wav`
- `data/recordings/<jobid>.snippet.wav`
- `data/transcripts/<jobid>.txt`
- `data/transcripts/<jobid>.json`
- `data/db/index.sqlite`
- `data/logs/app.log`
- `data/cache/` (Model cache) fileciteturn1file2turn1file3

### 9.2 SQLite Jobindex (MVP)
Speichert pro Job:
- status (internal job status kann granular sein)
- pfade
- timings
- model_info
- error_code + error_hint (keine PHI) fileciteturn1file2turn1file0turn1file3

### 9.3 Logging/PHI
- Keine Audio-/Textinhalte im Log
- nur Job-ID, Status, Laufzeiten, Fehlercodes fileciteturn1file3turn1file0

---

## 10. Konfiguration (config.toml, Defaultwerte)

Minimal:
- `audio.device` (Name/Index)
- `audio.samplerate = 16000`
- `audio.channels = 1`
- `snippet.seconds = 8`
- `stt.model = "small"`
- `stt.compute_type = "int8"`
- `stt.beam_size = 5`
- `stt.language = "de"`
- `retention.recordings_days = 7` (Beispiel)
- `retention.logs_days = 14` (Beispiel) fileciteturn1file2turn1file3turn1file1

---

## 11. Tests (MVP)

- Unit:
  - Audio-Qualität (stumm/clipping)
  - STT-Qualität (Metrik→Ampel)
- Integration:
  - Doctor/Preflight Script
  - Bench mit Fixture-Audio fileciteturn1file2turn1file0

---

## 12. Mapping: interne Job-States vs UI-States (nur zur Klarheit)

Interne Jobstates können granular sein (z.B. audio_saved, transcribing, partial_result), dürfen aber **nicht** die UI-States ersetzen.  
UI zeigt ausschließlich: READY/RECORDING/PAUSED/PROCESSING/DONE/ERROR. fileciteturn1file0turn1file1turn1file5
