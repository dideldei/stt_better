# STRUCTURE.md — Verbindliche Projektstruktur (No-Wildwuchs)

Dieses Dokument definiert die **einzige erlaubte Projektstruktur**.
Sie ist **verbindlich für Menschen und Coding-KIs**.

Bei Abweichungen gilt:
1. STRUCTURE.md
2. UNIFIED.md
3. TICKETS.md
4. AGENTS.md

---

## 1. Ziel der Struktur

- klare Verantwortlichkeiten
- minimale Kopplung
- einfache mentale Modelle
- **kein Wildwuchs**
- gute Lernbarkeit für Coding-KIs

Die Struktur folgt bewusst **keinen Framework-Trends**, sondern dem Projektbedarf.

---

## 2. Top-Level-Layout (verbindlich)

```text
stt-diktat-agent/
├─ README.md
├─ UNIFIED.md
├─ AGENTS.md
├─ TICKETS.md
├─ STRUCTURE.md
├─ pyproject.toml
├─ requirements.lock.txt
├─ .python-version
├─ .gitignore
├─ scripts/
├─ app/
├─ ui/
├─ services/
├─ domain/
├─ util/
├─ data/
├─ fixtures/
├─ tests/
└─ playground/
```

**Regel:**  
❌ Keine neuen Top-Level-Ordner ohne explizites Ticket.

---

## 3. Verantwortlichkeiten je Ordner

### `/app` — Orchestrierung & Wahrheit
**Enthält:**
- State Machine
- Job-Lifecycle
- Event-Dispatch
- zentrale Kontrolle

**Darf:**
- Services aufrufen
- Events erzeugen
- States wechseln

**Darf nicht:**
- UI rendern
- Audio/STT direkt implementieren

---

### `/ui` — Darstellung (Textual)
**Enthält:**
- Fokus-TUI
- Widgets
- Layout
- Keybindings

**Darf:**
- reactive Felder darstellen
- Events an `/app` senden

**Darf nicht:**
- Business-Logik enthalten
- Threads starten
- STT oder Audio aufrufen

---

### `/services` — I/O & externe Bibliotheken
**Enthält:**
- Audio-Capture (sounddevice)
- STT (faster-whisper)
- SQLite-Persistenz
- Qualitätsanalysen

**Darf:**
- Threads starten
- mit Hardware/Dateien sprechen

**Darf nicht:**
- Widgets anfassen
- UI-States setzen

---

### `/domain` — Reine Regeln & Typen
**Enthält:**
- Enums (States, Quality, Errors)
- Dataclasses
- konstante Regeln

**Darf:**
- von allen importiert werden

**Darf nicht:**
- I/O
- Threads
- Abhängigkeiten zu UI/Services

---

### `/util` — Kleine Hilfsfunktionen
**Enthält:**
- Pfad-Utilities
- Throttling
- Thread-Queues

**Darf:**
- trivial sein

**Darf nicht:**
- Logik duplizieren
- „heimliche“ Business-Regeln enthalten

---

### `/scripts` — Bedienung & Wartung
**Enthält:**
- Doctor / Preflight
- Run-Skripte
- Benchmarks

**Regel:**
- Skripte dürfen importieren, aber nichts Neues definieren.

---

### `/playground` — Lern- & Kata-Zone
**Enthält:**
- isolierte Experimente
- Pflicht-Katas (Textual)

**Regel:**
- Code aus `/playground` darf **nicht** direkt ins Produkt kopiert werden.
- Erst verstehen, dann neu schreiben.

---

### `/data` — Laufzeitdaten (gitignored)
**Enthält:**
- recordings/
- transcripts/
- db/
- logs/
- cache/

**Regel:**
- Keine PHI im Repo.
- Kein Commit von `/data`.

---

## 4. Querregeln (extrem wichtig)

### 4.1 Import-Regeln (Richtung!)
```text
domain  ←  util
   ↑         ↑
services    app
      ↑
      ui
```

- UI kennt **nur** `app`, `domain`, `util`
- Services kennen **kein** UI
- Domain kennt niemanden

---

### 4.2 Event-Regel
- Events werden **nur** in `app/events.py` definiert.
- Keine lokalen Event-Klassen.

---

### 4.3 Thread-Regel
- Threads nur in `/services`
- UI-Thread bleibt sauber
- Kommunikation nur über Events/Queues

---

## 5. Verbote (explizit)

❌ Neue Ordner „helpers“, „common“, „misc“  
❌ Logik in Widgets  
❌ Direkte STT-Aufrufe aus UI  
❌ Mehrere parallele Full-STT-Worker  
❌ Workarounds statt Ursachenanalyse  

---

## 6. Änderung der Struktur

Eine Änderung der Struktur erfordert:
- explizites Ticket
- Begründung
- Update von STRUCTURE.md

Ohne das: **Änderung unzulässig**.

---

## 7. Merksatz für Coding-KIs

> *„Wenn du nicht weißt, wohin etwas gehört, frag –  
> nicht raten, nicht neu erfinden.“*
