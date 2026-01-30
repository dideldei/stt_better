"""
Minimal test to understand Container + Vertical + Horizontal behavior
Following AGENTS.md: Minimalbeispiel → Verhalten verstehen → Integration
"""

from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Container, Horizontal, Vertical


class HeaderTest(App):
    CSS = """
    #test_container {
        height: 3;
        border: solid $primary;
    }
    
    #test_vertical {
        width: 1fr;
        height: 1fr;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Container(
            Vertical(
                Horizontal(
                    Static("Line 1 Part 1"),
                    Static("Line 1 Part 2"),
                ),
                Static("Line 2"),
                id="test_vertical"
            ),
            id="test_container"
        )


if __name__ == "__main__":
    app = HeaderTest()
    app.run()
