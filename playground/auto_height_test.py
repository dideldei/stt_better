"""Test 2: Container ohne fixed height (auto)"""
from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Container

class AutoHeightTest(App):
    CSS = """
    #test_container {
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
    app = AutoHeightTest()
    app.run()
