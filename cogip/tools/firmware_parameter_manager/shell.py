"""Interactive REPL for the firmware parameter manager.

Provides tab-completed `get` / `set` / `reset` / `reset-all` / `list` commands
over the firmware parameters declared in a sectioned YAML schema. The shell is
fully driven by the :class:`FirmwareParameterSchema` it receives; no parameter
name or section title is hardcoded here.
"""

from __future__ import annotations
import asyncio
import readline
import shlex
from collections.abc import Iterable

from pydantic import ValidationError

from cogip.models import FirmwareParameterSchema
from cogip.models.firmware_parameter import (
    FirmwareParameter,
    FirmwareParameterNotFound,
    FirmwareParameterValidationFailed,
)
from cogip.utils.console_ui import ConsoleUI
from .firmware_parameter_manager import FirmwareParameterManager

type ParameterValue = float | int | bool
type ParameterResult = ParameterValue | Exception

PROMPT = "fw-param> "

COMMANDS: tuple[str, ...] = ("list", "get", "set", "reset", "reset-all", "help", "exit", "quit")
NAME_COMMANDS: frozenset[str] = frozenset({"get", "set", "reset"})

DEFAULT_TIMEOUT = 2.0

UNAVAILABLE = "<unavailable>"
TIMEOUT = "<timeout>"


def parse_value(parameter: FirmwareParameter, raw_value: str) -> ParameterValue:
    """Convert a string to the type expected by the firmware parameter."""
    match parameter.value_obj.type:
        case "bool":
            lowered = raw_value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
            raise ValueError(f"invalid bool value: {raw_value!r}")
        case "float" | "double":
            return float(raw_value)
        case _:
            return int(raw_value)


def format_value(parameter: FirmwareParameter) -> str:
    type_name = parameter.value_obj.type
    if type_name in ("float", "double"):
        return f"{parameter.value:g}"
    return str(parameter.value)


class ParameterCompleter:
    """readline completer for `<command> [<param>] ...`."""

    def __init__(self, names: Iterable[str]) -> None:
        self._names: list[str] = sorted(names)
        self._matches: list[str] = []

    def update_names(self, names: Iterable[str]) -> None:
        self._names = sorted(names)

    def __call__(self, text: str, state: int) -> str | None:
        if state == 0:
            buffer = readline.get_line_buffer()
            begidx = readline.get_begidx()
            tokens_before = buffer[:begidx].split()
            if not tokens_before:
                pool: Iterable[str] = COMMANDS
            elif tokens_before[0] in NAME_COMMANDS and len(tokens_before) == 1:
                pool = self._names
            else:
                pool = ()
            self._matches = [c for c in pool if c.startswith(text)]
        if state < len(self._matches):
            return self._matches[state]
        return None


# Configure the readline binding once at import time so it is in place before
# any other UI activity (rich's Progress display in particular) touches the
# terminal. Only the completer instance is swapped at run-time.
#
# Python's `readline` module may be backed by either GNU readline or libedit
# (the latter is common on macOS and on some Linux Python builds). The two
# disagree on init-file syntax: GNU readline takes "tab: complete", libedit
# takes "bind ^I rl_complete". Without this branch tab completion silently
# does nothing on libedit systems.
readline.set_completer_delims(" \t\n")
if "libedit" in (readline.__doc__ or ""):
    readline.parse_and_bind("bind ^I rl_complete")
else:
    readline.parse_and_bind("tab: complete")


def _install_readline(completer: ParameterCompleter) -> None:
    readline.set_completer(completer)


async def _query_one(manager: FirmwareParameterManager, name: str) -> tuple[str, ParameterResult]:
    try:
        return name, await manager.get_parameter_value(name, timeout=DEFAULT_TIMEOUT)
    except Exception as exc:
        return name, exc


async def _snapshot(manager: FirmwareParameterManager, ui: ConsoleUI) -> tuple[dict[str, ParameterResult], set[str]]:
    """Query every parameter live and return (results, available_names)."""
    names = [p.name for p in manager.parameter_group]
    results: dict[str, ParameterResult] = {}
    tracker = ui.create_progress_tracker()
    tracker.start("[info]Querying firmware[/]", total=len(names))
    try:
        tasks = [asyncio.create_task(_query_one(manager, n)) for n in names]
        done = 0
        for fut in asyncio.as_completed(tasks):
            name, result = await fut
            results[name] = result
            done += 1
            tracker.update(completed=done)
    finally:
        tracker.stop()

    available = {name for name, result in results.items() if not isinstance(result, FirmwareParameterNotFound)}
    return results, available


def _format_snapshot_value(parameter: FirmwareParameter, result: ParameterResult) -> str:
    if isinstance(result, FirmwareParameterNotFound):
        return UNAVAILABLE
    if isinstance(result, TimeoutError):
        return TIMEOUT
    if isinstance(result, Exception):
        return f"<error: {type(result).__name__}>"
    return format_value(parameter)


def _show_snapshot(
    ui: ConsoleUI,
    schema: FirmwareParameterSchema,
    results: dict[str, ParameterResult],
) -> None:
    """Render every section as a single compact table separated by dividers."""
    table = ui.create_table(
        columns=[
            ("Parameter", {"style": "label", "no_wrap": True}),
            ("Value", {"style": "value", "justify": "right", "no_wrap": True}),
        ],
    )
    for index, section in enumerate(schema.sections):
        if not section.parameters:
            continue
        if index > 0:
            table.add_section()
        table.add_row(f"[phase]{section.title}[/]", "")
        for parameter in section.parameters:
            table.add_row(
                f"  {parameter.name}",
                _format_snapshot_value(parameter, results[parameter.name]),
            )
    ui.print(table)


def _show_help(ui: ConsoleUI) -> None:
    ui.show_panel(
        "[label]list[/]                       refresh and re-display every parameter\n"
        "[label]get <name>[/]                 read the current value from firmware\n"
        "[label]set <name> <value>[/]         write a new value\n"
        "[label]reset <name>[/]               restore the compile-time default\n"
        "[label]reset-all[/]                  reset every parameter\n"
        "[label]help[/]                       show this message\n"
        "[label]exit[/] | [label]quit[/] | [label]Ctrl-D[/]         leave the shell",
        title="Commands",
    )


def _report_command_error(ui: ConsoleUI, exc: Exception) -> None:
    if isinstance(exc, TimeoutError):
        ui.show_error("timeout — no response from firmware")
    elif isinstance(exc, FirmwareParameterValidationFailed):
        ui.show_error("rejected by firmware (read-only or out-of-bounds)")
    elif isinstance(exc, FirmwareParameterNotFound):
        ui.show_error("unknown to firmware (parameter not in CAN registry)")
    elif isinstance(exc, ValidationError):
        ui.show_error(f"invalid value: {exc.errors()[0]['msg']}")
    elif isinstance(exc, ValueError | KeyError):
        ui.show_error(str(exc))
    else:
        ui.show_error(f"{type(exc).__name__}: {exc}")


async def _cmd_get(manager: FirmwareParameterManager, ui: ConsoleUI, name: str) -> None:
    parameter = manager.parameter_group.get(name)
    await manager.get_parameter_value(name, timeout=DEFAULT_TIMEOUT)
    ui.show_key_value_table([(parameter.name, format_value(parameter))])


async def _cmd_set(manager: FirmwareParameterManager, ui: ConsoleUI, name: str, raw_value: str) -> None:
    parameter = manager.parameter_group.get(name)
    typed_value = parse_value(parameter, raw_value)
    await manager.set_parameter_value(name, typed_value, timeout=DEFAULT_TIMEOUT)
    ui.show_success(f"{name} = {format_value(parameter)}")


async def _cmd_reset(manager: FirmwareParameterManager, ui: ConsoleUI, name: str) -> None:
    await manager.reset_parameter_value(name, timeout=DEFAULT_TIMEOUT)
    ui.show_success(f"{name} reset to default")


async def _cmd_reset_all(manager: FirmwareParameterManager, ui: ConsoleUI) -> None:
    results = await manager.reset_all_parameters(timeout=DEFAULT_TIMEOUT)
    table = ui.create_table(
        columns=[
            ("Parameter", {"style": "label", "no_wrap": True}),
            ("Status", {"justify": "right", "no_wrap": True}),
        ],
    )
    for name, error in results.items():
        status = "[success]OK[/]" if error is None else f"[error]{type(error).__name__}[/]"
        table.add_row(name, status)
    ui.print(table)


async def _dispatch(
    line: str,
    manager: FirmwareParameterManager,
    ui: ConsoleUI,
    schema: FirmwareParameterSchema,
    completer: ParameterCompleter,
) -> bool:
    """Run a single command line. Returns False if the shell should exit."""
    try:
        tokens = shlex.split(line)
    except ValueError as exc:
        ui.show_error(f"parse error: {exc}")
        return True
    if not tokens:
        return True

    cmd, *args = tokens

    match cmd:
        case "exit" | "quit":
            return False
        case "help":
            _show_help(ui)
        case "list":
            results, available = await _snapshot(manager, ui)
            _show_snapshot(ui, schema, results)
            completer.update_names(available)
        case "reset-all":
            await _cmd_reset_all(manager, ui)
        case "get" | "set" | "reset":
            await _run_name_command(cmd, args, manager, ui)
        case _:
            ui.show_error(f"unknown command: {cmd!r}. Type 'help' for the list.")
    return True


async def _run_name_command(cmd: str, args: list[str], manager: FirmwareParameterManager, ui: ConsoleUI) -> None:
    """Execute one of the single-parameter commands (`get`/`set`/`reset`)."""
    if not args:
        ui.show_error(f"{cmd}: missing parameter name")
        return
    name = args[0]
    if name not in manager.parameter_group:
        ui.show_error(f"unknown parameter: {name!r}")
        return

    try:
        match cmd, args:
            case "get", [_]:
                await _cmd_get(manager, ui, name)
            case "set", [_, value]:
                await _cmd_set(manager, ui, name, value)
            case "reset", [_]:
                await _cmd_reset(manager, ui, name)
            case "set", _:
                ui.show_error("usage: set <name> <value>")
            case _:
                ui.show_error(f"{cmd} takes a single parameter name")
    except Exception as exc:
        _report_command_error(ui, exc)


async def run(
    manager: FirmwareParameterManager,
    ui: ConsoleUI,
    schema: FirmwareParameterSchema,
) -> None:
    """Run the interactive shell until the user exits."""
    all_names = [parameter.name for section in schema.sections for parameter in section.parameters]
    completer = ParameterCompleter(all_names)
    _install_readline(completer)

    ui.show_panel(
        "Firmware parameter manager — interactive shell.\n"
        "Type [label]list[/] to query every parameter, [label]help[/] for the full command list, "
        "[label]Tab[/] to complete.",
        title="firmware-parameter-manager",
    )

    while True:
        try:
            line = await asyncio.to_thread(input, PROMPT)
        except EOFError:
            ui.print()
            break
        except KeyboardInterrupt:
            ui.print()
            continue
        if not await _dispatch(line, manager, ui, schema, completer):
            break
