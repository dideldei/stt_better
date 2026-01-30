"""
Textual Update Kata - Ticket 0.1

Ziel: Beweis von Textual-Grundverständnis, unabhängig vom Projekt.
Architekturprinzipien (UNIFIED.md Punkt 3):
- UI-Thread fasst Widgets an, sonst niemand
- Background-Threads erzeugen nur Events
- Kommunikation ausschließlich über Events/Queue
- refresh() ist kein Fix
"""

import threading
import time
from textual.app import App, ComposeResult
from textual.widgets import Static, Log
from textual.message import Message


class LogUpdateMessage(Message):
    """Event für Log-Updates aus Background-Thread"""
    def __init__(self, message: str, thread_id: int) -> None:
        self.message = message
        self.thread_id = thread_id
        super().__init__()


class KataApp(App):
    """Minimal-UI mit Header (Status) und Log-Area"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #header_status {
        text-align: center;
        padding: 1;
        background: $primary;
        color: $text;
    }
    
    #log_area {
        height: 1fr;
        border: solid $primary;
    }
    """
    
    BINDINGS = [
        ("f1", "change_status", "Change Status (UI-Thread)"),
        ("f2", "start_background_task", "Start Background Task (10 Events)"),
        ("escape", "quit", "Quit"),
    ]
    
    def __init__(self) -> None:
        super().__init__()
        self.status_index = 0
        self.statuses = ["READY", "RECORDING", "PAUSED"]
        self.ui_thread_id = threading.get_native_id()
        self.background_thread = None
        self.background_running = False
    
    def compose(self) -> ComposeResult:
        """Erstellt die UI-Komponenten"""
        yield Static("Status: READY", id="header_status")
        yield Log(id="log_area")
    
    def on_mount(self) -> None:
        """Initialisiert die UI beim Start"""
        header = self.query_one("#header_status", Static)
        header.update(f"Status: {self.statuses[self.status_index]}")
        
        log = self.query_one("#log_area", Log)
        log.write(f"[UI-Thread {self.ui_thread_id}] App gestartet")
        log.write("Drücke F1: Status ändern (UI-Thread)")
        log.write("Drücke F2: Background-Task starten (10 Events)")
        log.write("Drücke Esc: Beenden")
    
    def action_change_status(self) -> None:
        """F1: Status ändern im UI-Thread (sofort sichtbar)"""
        current_thread_id = threading.get_native_id()
        log = self.query_one("#log_area", Log)
        log.write(f"[UI-Thread {current_thread_id}] F1 gedrückt - Status ändern")
        
        # Status rotieren
        self.status_index = (self.status_index + 1) % len(self.statuses)
        new_status = self.statuses[self.status_index]
        
        # Widget direkt im UI-Thread aktualisieren
        header = self.query_one("#header_status", Static)
        header.update(f"Status: {new_status}")
        
        log.write(f"[UI-Thread {current_thread_id}] Status geändert zu: {new_status}")
    
    def action_start_background_task(self) -> None:
        """F2: Background-Task starten (10 Events, 1/s)"""
        if self.background_running:
            log = self.query_one("#log_area", Log)
            log.write("[UI-Thread] Background-Task läuft bereits")
            return
        
        log = self.query_one("#log_area", Log)
        log.write(f"[UI-Thread {self.ui_thread_id}] F2 gedrückt - Background-Task starten")
        
        self.background_running = True
        self.background_thread = threading.Thread(
            target=self._background_worker,
            daemon=True,
            name="BackgroundWorker"
        )
        self.background_thread.start()
    
    def _background_worker(self) -> None:
        """Background-Thread: erzeugt 10 Events (1/s)"""
        background_thread_id = threading.get_native_id()
        
        # Thread-sichere Event-Übergabe an UI-Thread
        for i in range(10):
            time.sleep(1.0)  # 1 Event pro Sekunde
            
            message = f"Event {i+1}/10 aus Background-Thread"
            # call_from_thread() sendet Event sicher an UI-Thread
            self.call_from_thread(
                self.post_message,
                LogUpdateMessage(message, background_thread_id)
            )
        
        # Abschluss-Event
        self.call_from_thread(
            self.post_message,
            LogUpdateMessage("Background-Task abgeschlossen", background_thread_id)
        )
        self.background_running = False
    
    def on_log_update_message(self, event: LogUpdateMessage) -> None:
        """Event-Handler: verarbeitet Log-Updates im UI-Thread"""
        current_thread_id = threading.get_native_id()
        log = self.query_one("#log_area", Log)
        
        # Zeige Thread-Trennung in Logs
        log.write(
            f"[UI-Thread {current_thread_id}] "
            f"Empfangen von Background-Thread {event.thread_id}: {event.message}"
        )
        log.write(
            f"  → Thread-Trennung: UI-Thread ({current_thread_id}) ≠ "
            f"Background-Thread ({event.thread_id})"
        )


def main():
    """Hauptfunktion zum Starten der Kata-App"""
    app = KataApp()
    app.run()


if __name__ == "__main__":
    main()
