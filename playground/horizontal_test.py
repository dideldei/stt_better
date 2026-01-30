"""Test 3: Horizontal-Container mit mehreren Static-Widgets"""
from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal

class HorizontalTest(App):
    CSS = """
    Horizontal {
        width: 1fr;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("Part 1"),
            Static("Part 2"),
            Static("Part 3"),
        )

if __name__ == "__main__":
    app = HorizontalTest()
    app.run()
