import asyncio
from dataclasses import dataclass, field

import socketio

from cogip.models import AnnouncedParameter, FirmwareParametersGroup, ParameterTag, ParameterType
from . import logger
from .sio_events import SioEvents

_ONEOF_FIELD_BY_TYPE: dict[ParameterType, str] = {
    ParameterType.FLOAT: "float_value",
    ParameterType.DOUBLE: "double_value",
    ParameterType.INT32: "int32_value",
    ParameterType.UINT32: "uint32_value",
    ParameterType.INT64: "int64_value",
    ParameterType.UINT64: "uint64_value",
    ParameterType.BOOL: "bool_value",
}


def _extract_scalar(
    pb_value: dict,
    type: ParameterType,
) -> float | int | bool | None:
    """Pull the scalar matching a ParameterType out of a PB_ParameterValue dict.

    The CAN -> MessageToDict round-trip always emits every oneof candidate
    because the copilot uses `always_print_fields_with_no_presence=True`; we
    pick the one that matches the announced scalar type.
    """
    if not pb_value:
        return None
    field_name = _ONEOF_FIELD_BY_TYPE.get(type)
    if field_name is None:
        return None
    return pb_value.get(field_name)


@dataclass
class _PartialAnnouncedParameter:
    """Running reassembly state for one announced parameter.

    Header / name / bounds arrive in separate SIO events; the aggregator
    stitches them together here and converts the entry to AnnouncedParameter
    once it has everything it needs (bounds are only required when the header
    flagged has_bounds).
    """

    board_id: int | None = None
    key_hash: int | None = None
    type: ParameterType | None = None
    tags: set[ParameterTag] = field(default_factory=set)
    read_only: bool = False
    has_bounds: bool = False
    # Flags set as each frame arrives:
    has_header: bool = False
    has_name: bool = False
    has_bounds_data: bool = False
    # Reassembled payload:
    name: str | None = None
    min_value: float | int | bool | None = None
    max_value: float | int | bool | None = None

    @property
    def complete(self) -> bool:
        if not (self.has_header and self.has_name):
            return False
        if self.has_bounds and not self.has_bounds_data:
            return False
        return True

    def to_announced(self) -> AnnouncedParameter:
        assert self.complete
        return AnnouncedParameter(
            board_id=self.board_id,
            key_hash=self.key_hash,
            name=self.name,
            type=self.type,
            tags=self.tags,
            read_only=self.read_only,
            has_bounds=self.has_bounds,
            min_value=self.min_value,
            max_value=self.max_value,
        )


class _AnnounceAggregator:
    """Collect announce frames until every responding board is done.

    The host does not know up-front which boards will answer. Each header
    carries `board_id` and `total_count`; the aggregator learns the set of
    boards and their expected counts from the first header per board, and
    resolves the future when every known board has delivered `total_count`
    fully-reassembled entries (or when the caller's timeout fires).
    """

    def __init__(self, tag_filter: ParameterTag):
        self.tag_filter = tag_filter
        self.partials: dict[int, _PartialAnnouncedParameter] = {}  # keyed by key_hash
        self.expected_per_board: dict[int, int] = {}
        self.complete_per_board: dict[int, int] = {}
        self.future: asyncio.Future[list[AnnouncedParameter]] = asyncio.Future()

    def _partial_for(self, key_hash: int) -> _PartialAnnouncedParameter:
        return self.partials.setdefault(key_hash, _PartialAnnouncedParameter())

    def _notify_partial_complete(self, partial: _PartialAnnouncedParameter) -> None:
        if partial.board_id is None:
            return
        self.complete_per_board[partial.board_id] = self.complete_per_board.get(partial.board_id, 0) + 1

    def _maybe_resolve(self) -> None:
        if self.future.done():
            return
        if not self.expected_per_board:
            return
        for board_id, expected in self.expected_per_board.items():
            if self.complete_per_board.get(board_id, 0) < expected:
                return
        self.future.set_result(self._collect())

    def _collect(self) -> list[AnnouncedParameter]:
        return [p.to_announced() for p in self.partials.values() if p.complete]

    def resolve_partial_on_timeout(self) -> list[AnnouncedParameter]:
        """Called by the caller when the timeout fires."""
        missing = [
            (board_id, expected - self.complete_per_board.get(board_id, 0))
            for board_id, expected in self.expected_per_board.items()
            if self.complete_per_board.get(board_id, 0) < expected
        ]
        if missing:
            logger.warning(f"Announce timeout with incomplete boards: {missing}")
        return self._collect()

    # Event handlers (invoked by SioEvents):

    def on_header(
        self,
        board_id: int,
        key_hash: int,
        type: ParameterType,
        tags: set[ParameterTag],
        read_only: bool,
        has_bounds: bool,
        total_count: int,
        index: int,
    ) -> None:
        if board_id not in self.expected_per_board:
            self.expected_per_board[board_id] = total_count
        partial = self._partial_for(key_hash)
        was_complete = partial.complete
        partial.board_id = board_id
        partial.key_hash = key_hash
        partial.type = type
        partial.tags = tags
        partial.read_only = read_only
        partial.has_bounds = has_bounds
        partial.has_header = True
        if partial.complete and not was_complete:
            self._notify_partial_complete(partial)
        self._maybe_resolve()

    def on_name(self, key_hash: int, name: str) -> None:
        partial = self._partial_for(key_hash)
        was_complete = partial.complete
        partial.name = name
        partial.has_name = True
        if partial.complete and not was_complete:
            self._notify_partial_complete(partial)
        self._maybe_resolve()

    def on_bounds(
        self, key_hash: int, min_value: float | int | bool | None, max_value: float | int | bool | None
    ) -> None:
        partial = self._partial_for(key_hash)
        was_complete = partial.complete
        partial.min_value = min_value
        partial.max_value = max_value
        partial.has_bounds_data = True
        if partial.complete and not was_complete:
            self._notify_partial_complete(partial)
        self._maybe_resolve()


class FirmwareParameterManager:
    """
    Manager to handle firmware parameter requests/responses via SocketIO through copilot.
    Uses asyncio.Future to correlate requests with their responses.

    This class is designed to be embedded into another Socket.IO client (e.g., Planner,
    Monitor, or any tool that needs firmware parameter access). It registers its own
    namespace (/parameters) on the provided client, allowing the host tool to manage
    the connection lifecycle while benefiting from firmware parameter functionality.

    Note on concurrent usage: The correlation mechanism uses parameter hashes (FNV-1a)
    to match responses to requests. This makes the system naturally resilient to multiple
    clients making concurrent requests - each client maintains its own pending requests
    dictionary and only resolves its own Futures. However, this usage pattern is not
    recommended as it may lead to unpredictable firmware behavior and debugging complexity.
    Prefer having a single client handle firmware parameters at a time.
    """

    def __init__(
        self,
        sio: socketio.AsyncClient,
        parameter_group: FirmwareParametersGroup,
    ):
        """
        Initialize the FirmwareParameterManager.

        Args:
            sio: External Socket.IO client on which to register the /parameters namespace.
                 The host client is responsible for connection management.
            parameter_group: The firmware parameters to manage
        """
        self.sio = sio
        self.parameter_group = parameter_group

        self.sio_events = SioEvents(self)
        self.sio.register_namespace(self.sio_events)

        # Dictionary to store Futures waiting for responses
        # Key: firmware parameter hash (int), Value: asyncio.Future
        self.pending_get_requests: dict[int, asyncio.Future] = {}
        self.pending_set_requests: dict[int, asyncio.Future] = {}

        # Announce aggregator: only one announce is ever active at a time, so
        # concurrent announce() calls serialize via self._announce_lock.
        self._announce_lock = asyncio.Lock()
        self._active_announce: _AnnounceAggregator | None = None

        # Cache of the most recent announce, keyed by key_hash. Populated by
        # announce(); tools can use it to avoid re-announcing when the
        # firmware registry is stable.
        self.announced_cache: dict[int, AnnouncedParameter] = {}

    @property
    def namespace(self) -> str:
        """Return the namespace path to include when connecting the host client."""
        return self.sio_events.namespace

    @property
    def is_connected(self) -> bool:
        """Check if the namespace is connected and ready."""
        return self.sio_events.connected

    async def get_parameter_value(
        self,
        parameter_name: str,
        timeout: float = 1,
    ) -> float | int | bool:
        """
        Sends a get_firmware_parameter request and waits for the response.

        Args:
            parameter_name: Name of the firmware parameter to retrieve
            timeout: Timeout in seconds (default: 1)

        Returns:
            The firmware parameter value (float, int, or bool) after pydantic validation

        Raises:
            KeyError: If the firmware parameter name is not found in the firmware parameter group
            TimeoutError: If no response is received within the timeout
        """
        # Validate that firmware parameter exists in the group
        parameter = self.parameter_group.get(parameter_name)

        # Create a Future for this request
        future = asyncio.Future()

        # Store pending request for response correalation
        parameter_hash = hash(parameter)
        self.pending_get_requests[parameter_hash] = future

        try:
            logger.info(f"[firmware_parameter => server] get: {parameter}")
            await self.sio.emit("get_parameter_value", parameter.model_dump(by_alias=True), namespace="/parameters")

            logger.info(f"Sent get_parameter request for hash: 0x{parameter_hash:08x}")

            # Wait for the response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)

            # Update parameter with response data (pydantic validation happens here)
            parameter.pb_read(response)

            # Return the validated value
            return parameter.value

        except TimeoutError:
            # Clean up on timeout
            if not future.done():
                future.cancel()

            self.pending_get_requests.pop(parameter_hash, None)
            logger.error(f"Timeout waiting for get_firmware_parameter response (hash: 0x{parameter_hash:08x})")
            raise TimeoutError(f"No response received for firmware parameter hash 0x{parameter_hash:08x}")

        except Exception as exc:
            # Clean up on error
            if not future.done():
                future.cancel()

            self.pending_get_requests.pop(parameter_hash, None)
            logger.error(f"Error in get_parameter: {exc}")
            raise

    async def set_parameter_value(
        self,
        parameter_name: str,
        value: int | float | bool,
        timeout: float = 1,
    ) -> None:
        """
        Sends a set_firmware_parameter request and waits for the response.

        Args:
            parameter_name: Name of the firmware parameter to modify
            value: Value to set (int, float, or bool)
            timeout: Timeout in seconds (default: 1)

        Returns:
            True if the firmware parameter was successfully written

        Raises:
            KeyError: If the firmware parameter name is not found in the firmware parameter group
            ValidationError: If the value type doesn't match the firmware parameter type or is invalid
            TimeoutError: If no response is received within the timeout
        """
        # Validate that firmware parameter exists in the group
        parameter = self.parameter_group.get(parameter_name)

        # Set the new value (pydantic validation happens here)
        parameter.value = value

        # Create a Future for this request
        future = asyncio.Future()

        # Store pending request for response correalation
        parameter_hash = hash(parameter)
        self.pending_set_requests[parameter_hash] = future

        try:
            logger.info(f"[firmware_parameter => server] set: {parameter}")
            await self.sio.emit("set_parameter_value", parameter.model_dump(by_alias=True), namespace="/parameters")

            logger.info(f"Sent set_parameter request for hash: 0x{parameter_hash:08x}")

            # Wait for the response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)

            # Update parameter with response data (pydantic validation happens here)
            parameter.pb_read(response)

        except TimeoutError:
            # Clean up on timeout
            if not future.done():
                future.cancel()

            self.pending_set_requests.pop(parameter_hash, None)
            logger.error(f"Timeout waiting for set_firmware_parameter response (hash: 0x{parameter_hash:08x})")
            raise TimeoutError(f"No response received for firmware parameter hash 0x{parameter_hash:08x}")

        except Exception as exc:
            # Clean up on error
            if not future.done():
                future.cancel()

            self.pending_set_requests.pop(parameter_hash, None)
            logger.error(f"Error in set_parameter: {exc}")
            raise

    async def announce(
        self,
        tag: ParameterTag = ParameterTag.NONE,
        timeout: float = 3.0,
    ) -> list[AnnouncedParameter]:
        """Ask every firmware board to announce the parameters matching `tag`.

        One announce request is sent on the CAN bus; every responding board
        streams a header + name (+ optional bounds) frame per parameter. The
        aggregator reassembles by key_hash and resolves once every board has
        delivered the `total_count` entries it promised in its headers, or at
        `timeout` with whatever was completed so far.

        Args:
            tag: Tag filter; ParameterTag.NONE returns every parameter.
            timeout: Max seconds to wait for the announce to complete.

        Returns:
            List of fully-reassembled AnnouncedParameter instances. Entries
            that did not complete before timeout are dropped with a warning.
        """
        async with self._announce_lock:
            aggregator = _AnnounceAggregator(tag)
            self._active_announce = aggregator

            try:
                logger.info(f"[firmware_parameter => server] announce (tag={tag.name})")
                await self.sio.emit(
                    "parameter_announce_request",
                    {"tag_filter": int(tag)},
                    namespace="/parameters",
                )

                try:
                    result = await asyncio.wait_for(aggregator.future, timeout=timeout)
                except TimeoutError:
                    if not aggregator.future.done():
                        aggregator.future.cancel()
                    result = aggregator.resolve_partial_on_timeout()

                for param in result:
                    self.announced_cache[param.key_hash] = param
                return result
            finally:
                self._active_announce = None

    def _ingest_announce_header(self, payload: dict) -> None:
        """Feed a header frame into the active aggregator, if any."""
        if self._active_announce is None:
            logger.warning("Received announce_header with no active announce")
            return
        try:
            type_ = ParameterType(int(payload.get("type", 0)))
            tags_bitmask = int(payload.get("tags_bitmask", 0))
            tags = {t for t in ParameterTag if t != ParameterTag.NONE and (tags_bitmask & (1 << int(t)))}
            flags = int(payload.get("flags", 0))
            self._active_announce.on_header(
                board_id=int(payload["board_id"]),
                key_hash=int(payload["key_hash"]),
                type=type_,
                tags=tags,
                read_only=bool(flags & 0x1),
                has_bounds=bool(flags & 0x2),
                total_count=int(payload.get("total_count", 0)),
                index=int(payload.get("index", 0)),
            )
        except Exception as exc:
            logger.error(f"Invalid announce_header payload {payload}: {exc}")

    def _ingest_announce_name(self, payload: dict) -> None:
        """Feed a name frame into the active aggregator, if any."""
        if self._active_announce is None:
            logger.warning("Received announce_name with no active announce")
            return
        try:
            self._active_announce.on_name(
                key_hash=int(payload["key_hash"]),
                name=str(payload.get("name", "")),
            )
        except Exception as exc:
            logger.error(f"Invalid announce_name payload {payload}: {exc}")

    def _ingest_announce_bounds(self, payload: dict) -> None:
        """Feed a bounds frame into the active aggregator, if any."""
        if self._active_announce is None:
            logger.warning("Received announce_bounds with no active announce")
            return
        try:
            key_hash = int(payload["key_hash"])
            partial = self._active_announce.partials.get(key_hash)
            # Without a prior header we don't know the scalar type; default to
            # FLOAT as a best-effort (bounds will still be usable if floats).
            type_ = partial.type if (partial and partial.type is not None) else ParameterType.FLOAT
            min_value = _extract_scalar(payload.get("min_value", {}) or {}, type_)
            max_value = _extract_scalar(payload.get("max_value", {}) or {}, type_)
            self._active_announce.on_bounds(key_hash, min_value, max_value)
        except Exception as exc:
            logger.error(f"Invalid announce_bounds payload {payload}: {exc}")

    def cleanup(self):
        """
        Cleans up all pending Futures.
        """
        for future in self.pending_get_requests.values():
            if not future.done():
                future.cancel()
        for future in self.pending_set_requests.values():
            if not future.done():
                future.cancel()

        self.pending_get_requests.clear()
        self.pending_set_requests.clear()

        if self._active_announce is not None and not self._active_announce.future.done():
            self._active_announce.future.cancel()
        self._active_announce = None
