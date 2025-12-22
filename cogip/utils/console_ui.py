"""
Generic Console UI components using Rich.

Provides a themed console interface with consistent styling
for interactive CLI tools.
"""

from __future__ import annotations
import asyncio
from typing import Any

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, ProgressColumn, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.theme import Theme


class CustomProgressTracker:
    """
    Progress tracker with manual lifecycle and custom columns/fields.

    Features:
    - Manual start/update/stop control
    - Custom Rich columns
    - Custom task fields that can be updated

    Example:
        tracker = console.create_progress_tracker(columns=[
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TextColumn("Status: {task.fields[status]}"),
        ])
        tracker.start("Processing", total=100, status="starting")
        for i in range(100):
            tracker.update(completed=i, status=f"item {i}")
        tracker.stop()
    """

    def __init__(
        self,
        console: Console,
        columns: list[ProgressColumn] | None = None,
    ):
        """
        Initialize the progress tracker.

        Args:
            console: Console instance for output
            columns: Custom Rich Progress columns. If None, uses default columns.
        """
        self._console = console
        self._columns = columns or [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ]
        self._progress: Progress | None = None
        self._task_id: TaskID | None = None

    def start(
        self,
        description: str,
        total: float = 100,
        **fields: float,
    ) -> None:
        """
        Start the progress display.

        Args:
            description: Task description
            total: Total value for 100% completion (default: 100 for percentage)
            **fields: Custom fields to display
        """
        if self._progress is not None:
            raise RuntimeError("Progress already started. Call stop() first.")

        self._progress = Progress(*self._columns, console=self._console)
        self._progress.start()
        self._task_id = self._progress.add_task(description, total=total, **fields)

    def update(
        self,
        *,
        completed: float | None = None,
        description: str | None = None,
        **fields: float,
    ) -> None:
        """
        Update progress state.

        Args:
            completed: Current completion value (0 to total)
            description: New description (optional)
            **fields: Updated custom field values
        """
        if self._progress is None or self._task_id is None:
            return

        self._progress.update(
            self._task_id,
            completed=completed,
            description=description,
            **fields,
        )

    def stop(self, complete: bool = True) -> None:
        """
        Stop the progress display.

        Args:
            complete: If True, set progress to 100% before stopping
        """
        if self._progress is None:
            return

        if complete and self._task_id is not None:
            self._progress.update(self._task_id, completed=self._progress.tasks[self._task_id].total)

        self._progress.stop()
        self._progress = None
        self._task_id = None

    @property
    def is_active(self) -> bool:
        """Check if progress is currently active."""
        return self._progress is not None


DEFAULT_THEME = Theme(
    {
        # Primary styles - using Rich default colors
        "header": "bold cyan",
        "phase": "bold bright_white",
        "value": "bold bright_cyan",
        "label": "white",
        # Status styles
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "info": "bright_blue",
        # Utility
        "muted": "dim",
        "prompt": "bold yellow",
    }
)


class ConsoleUI(Console):
    """Generic console UI with themed output and async input methods."""

    def __init__(self, theme: Theme | None = None):
        """
        Initialize the console UI.

        Args:
            theme: Custom Rich theme. If None, uses DEFAULT_THEME.
        """
        super().__init__(theme=theme or DEFAULT_THEME)

    def show_panel(
        self,
        content: str,
        *,
        title: str | None = None,
        subtitle: str | None = None,
        border_style: str = "header",
    ) -> None:
        """
        Display a styled panel.

        Args:
            content: Panel content text
            title: Optional panel title
            subtitle: Optional panel subtitle
            border_style: Border style name from theme
        """
        self.print(
            Panel(
                content,
                title=f"[header]{title}[/]" if title else None,
                subtitle=f"[muted]{subtitle}[/]" if subtitle else None,
                border_style=border_style,
                box=ROUNDED,
                padding=(1, 2),
            )
        )

    def show_rule(self, title: str, *, style: str = "muted", title_style: str = "phase") -> None:
        """
        Display a horizontal rule with title.

        Args:
            title: Rule title text
            style: Line style name from theme
            title_style: Title style name from theme
        """
        self.print()
        self.print(Rule(f"[{title_style}]{title}[/]", style=style))
        self.print()

    def show_success(self, message: str) -> None:
        """Display a success message."""
        self.print(f"[success]\u2713 {message}[/]")

    def show_warning(self, message: str) -> None:
        """Display a warning message."""
        self.print(f"[warning]\u26a0 {message}[/]")

    def show_error(self, message: str) -> None:
        """Display an error message."""
        self.print(f"[error]\u2717 {message}[/]")

    def show_info(self, message: str) -> None:
        """Display an info message."""
        self.print(f"[muted]\u2139 {message}[/]")

    def create_table(
        self,
        title: str | None = None,
        columns: list[tuple[str, dict[str, Any]]] | None = None,
    ) -> Table:
        """Create a styled table.

        Args:
            title: Optional table title
            columns: List of (name, kwargs) tuples for columns.
                     kwargs are passed to add_column().

        Returns:
            Configured Table instance ready for add_row() calls.
        """
        table = Table(
            title=f"[phase]{title}[/]" if title else None,
            box=ROUNDED,
            border_style="muted",
            header_style="header",
            show_header=True,
            padding=(0, 1),
        )
        if columns:
            for name, kwargs in columns:
                table.add_column(name, **kwargs)
        return table

    def show_key_value_table(
        self,
        data: list[tuple[str, str]],
        title: str | None = None,
        key_header: str = "Parameter",
        value_header: str = "Value",
    ) -> None:
        """Display a simple key-value table.

        Args:
            data: List of (key, value) tuples
            title: Optional table title
            key_header: Header for key column
            value_header: Header for value column
        """
        table = self.create_table(
            title=title,
            columns=[
                (key_header, {"style": "label"}),
                (value_header, {"style": "value", "justify": "right"}),
            ],
        )
        for key, value in data:
            table.add_row(key, value)
        self.print(table)

    def show_comparison_table(
        self,
        data: list[tuple[str, str, str]],
        title: str | None = None,
        key_header: str = "Parameter",
        before_header: str = "Previous",
        after_header: str = "New",
    ) -> None:
        """Display a before/after comparison table.

        Args:
            data: List of (key, before_value, after_value) tuples
            title: Optional table title
            key_header: Header for key column
            before_header: Header for before column
            after_header: Header for after column
        """
        table = self.create_table(
            title=title,
            columns=[
                (key_header, {"style": "label"}),
                (before_header, {"style": "muted"}),
                (after_header, {"style": "value"}),
            ],
        )
        for key, before, after in data:
            table.add_row(key, before, after)
        self.print(table)

    async def get_string(self, prompt: str, *, default: str | None = None) -> str:
        """
        Get string input from user.

        Args:
            prompt: Prompt message to display
            default: Default value. If None, input is required.
        """
        kwargs: dict[str, Any] = {"console": self}
        if default is not None:
            kwargs["default"] = default
        return await asyncio.to_thread(lambda: Prompt.ask(f"[prompt]{prompt}[/]", **kwargs))

    async def get_integer(self, prompt: str, *, default: int | None = None) -> int:
        """
        Get integer input from user.

        Displays a confirmation message with the chosen value.

        Args:
            prompt: Prompt message to display
            default: Default value. If None, input is required.
        """
        kwargs: dict[str, Any] = {"console": self}
        if default is not None:
            kwargs["default"] = default
        value = await asyncio.to_thread(lambda: IntPrompt.ask(f"[prompt]{prompt}[/]", **kwargs))
        self.show_info(f"Chosen: {value}")
        return value

    async def get_float(self, prompt: str, *, default: float | None = None) -> float:
        """
        Get float input from user.

        Args:
            prompt: Prompt message to display
            default: Default value. If None, input is required.
        """
        kwargs: dict[str, Any] = {"console": self}
        if default is not None:
            kwargs["default"] = default
        return await asyncio.to_thread(lambda: FloatPrompt.ask(f"[prompt]{prompt}[/]", **kwargs))

    async def confirm(self, message: str, *, default: bool = True) -> bool:
        """
        Ask for confirmation.

        Args:
            message: Confirmation message to display
            default: Default value when user presses Enter
        """
        return await asyncio.to_thread(lambda: Confirm.ask(f"[header]{message}[/]", default=default, console=self))

    async def wait_for_enter(self, message: str) -> None:
        """
        Wait for user to press Enter.

        Args:
            message: Message to display before waiting
        """
        await asyncio.to_thread(lambda: self.input(f"[prompt]{message}[/] [muted][[Enter]][/] "))

    def create_progress_tracker(
        self,
        columns: list[ProgressColumn] | None = None,
    ) -> CustomProgressTracker:
        """
        Create a progress tracker with manual lifecycle control.

        Features:
        - Custom display columns
        - Custom updatable fields
        - Manual start/update/stop control

        Args:
            columns: Custom Rich Progress columns. If None, uses default columns
                    (spinner, description, bar, percentage, elapsed time).

        Returns:
            CustomProgressTracker instance (call .start() to begin tracking)
        """
        return CustomProgressTracker(self, columns)


if __name__ == "__main__":
    import time

    async def demo() -> None:
        """Demonstrate ConsoleUI features."""
        ui = ConsoleUI()

        # Welcome panel
        ui.show_panel(
            "This demo showcases all features of the ConsoleUI class.\n"
            "Follow the prompts to see each feature in action.",
            title="Console UI Demo",
            subtitle="Interactive demonstration",
        )

        # Status messages
        ui.show_rule("Status Messages")
        ui.show_success("Operation completed successfully")
        ui.show_warning("This is a warning message")
        ui.show_error("This is an error message")
        ui.show_info("This is an informational message")

        # Key-value table
        ui.show_rule("Key-Value Table")
        ui.show_key_value_table(
            [
                ("Robot ID", "1"),
                ("Wheel diameter", "60.0 mm"),
                ("Encoder resolution", "4096 ticks"),
                ("Max speed", "1000 mm/s"),
            ],
            title="Robot Configuration",
        )

        # Comparison table
        ui.show_rule("Comparison Table")
        ui.show_comparison_table(
            [
                ("Left wheel", "59.8 mm", "60.2 mm"),
                ("Right wheel", "60.1 mm", "59.9 mm"),
                ("Track width", "280.0 mm", "281.5 mm"),
            ],
            title="Calibration Results",
            before_header="Before",
            after_header="After",
        )

        # Custom table
        ui.show_rule("Custom Table")
        table = ui.create_table(
            title="Sensor Readings",
            columns=[
                ("Sensor", {"style": "label"}),
                ("Value", {"style": "value", "justify": "right"}),
                ("Status", {"style": "success", "justify": "center"}),
            ],
        )
        table.add_row("Temperature", "25.3°C", "OK")
        table.add_row("Battery", "12.4V", "OK")
        table.add_row("Distance", "150 mm", "OK")
        ui.print(table)

        # Interactive inputs
        ui.show_rule("Interactive Inputs")

        robot_name = await ui.get_string("Robot name", default="PAMI")
        ui.show_info(f"Configuring robot: {robot_name}")

        robot_id = await ui.get_integer("Robot ID (1-4)", default=1)
        ui.show_info(f"Robot ID set to: {robot_id}")

        wheel_diameter = await ui.get_float("Wheel diameter (mm)", default=60.0)
        ui.show_info(f"Wheel diameter: {wheel_diameter:.1f} mm")

        confirmed = await ui.confirm("Do you want to continue?", default=True)
        if confirmed:
            ui.show_success("Continuing...")
        else:
            ui.show_warning("Cancelled by user")

        # Progress tracker demo
        ui.show_rule("Progress Tracker Demo")
        tracker = ui.create_progress_tracker()
        tracker.start("[info]Processing items[/]", total=10)
        for i in range(10):
            time.sleep(0.3)
            tracker.update(completed=i + 1)
        tracker.stop()
        ui.show_success("Progress tracker demo complete")

        # Final panel
        await ui.wait_for_enter("Press Enter to exit")
        ui.show_panel(
            "[success]All features demonstrated successfully![/]",
            title="Demo Complete",
            border_style="success",
        )

    asyncio.run(demo())
