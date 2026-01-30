"""Test 1: Container mit zwei Static-Widgets (kein Horizontal, kein Vertical)"""
from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Container

class SimpleTest(App):
    CSS = """
    #test_container {
        height: 3;
        border: solid $primary;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("Zeile 1"),
            Static("Zeile 2"),
            id="test_container"
        )

if __name__ == "__main__":
    app = SimpleTest()
    app.run()
