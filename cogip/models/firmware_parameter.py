from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    RootModel,
    Strict,
    StrictBool,
    StrictFloat,
    StrictInt,
)

from cogip.protobuf import (
    PB_ParameterGetRequest,
    PB_ParameterGetResponse,
    PB_ParameterSetRequest,
    PB_ParameterSetResponse,
    PB_ParameterStatus,
)
from cogip.utils.fnv1a import fnv1a_hash


class FirmwareParameterValidationFailed(Exception):
    """Exception raised when firmware parameter validation fails.

    This exception is raised when a firmware parameter value does not meet
    the validation constraints defined for that parameter value range on the embedded side.
    """

    pass


class FirmwareParameterNotFound(Exception):
    """Exception raised when a requested firmware parameter is not found.

    This exception is raised when trying to access or modify a firmware parameter
    that does not exist in the parameter registry on the embedded side.
    """

    pass


class FirmwareParameterBase(BaseModel):
    """Base firmware parameter type"""

    model_config = ConfigDict(validate_assignment=True)


class FirmwareParameterFloat(FirmwareParameterBase):
    """Float firmware parameter value."""

    type: Literal["float"] = "float"
    content: StrictFloat


class FirmwareParameterDouble(FirmwareParameterBase):
    """Double firmware parameter value."""

    type: Literal["double"] = "double"
    content: StrictFloat


class FirmwareParameterInt32(FirmwareParameterBase):
    """Signed 32-bit integer firmware parameter value."""

    type: Literal["int32"] = "int32"
    content: StrictInt


class FirmwareParameterUInt32(FirmwareParameterBase):
    """Unsigned 32-bit integer firmware parameter value."""

    type: Literal["uint32"] = "uint32"
    content: Annotated[NonNegativeInt, Strict()]


class FirmwareParameterInt64(FirmwareParameterBase):
    """Signed 64-bit integer firmware parameter value."""

    type: Literal["int64"] = "int64"
    content: StrictInt


class FirmwareParameterUInt64(FirmwareParameterBase):
    """Unsigned 64-bit integer firmware parameter value."""

    type: Literal["uint64"] = "uint64"
    content: Annotated[NonNegativeInt, Strict()]


class FirmwareParameterBool(FirmwareParameterBase):
    """Boolean firmware parameter value."""

    type: Literal["bool"] = "bool"
    content: StrictBool


# Discriminated union of all firmware parameter value types
FirmwareParameterValueType = (
    FirmwareParameterFloat
    | FirmwareParameterDouble
    | FirmwareParameterInt32
    | FirmwareParameterUInt32
    | FirmwareParameterInt64
    | FirmwareParameterUInt64
    | FirmwareParameterBool
)


class FirmwareParameter(BaseModel):
    """Firmware parameter model with discriminated union for type-safe values.

    Attributes:
        name: The firmware parameter name
        value: The firmware parameter content value (float, int, or bool)
        value_obj: The firmware parameter value object with its type
    """

    model_config = ConfigDict(validate_assignment=True)

    name: str
    value_obj: Annotated[FirmwareParameterValueType, Field(alias="value", discriminator="type")]

    def __hash__(self):
        return fnv1a_hash(self.name)

    @property
    def value(self) -> float | int | bool:
        """Get the firmware parameter content value.

        Returns:
            The actual content value (float, int, or bool)
        """
        return self.value_obj.content

    @value.setter
    def value(self, content: float | int | bool) -> None:
        """Set the firmware parameter content value.

        Args:
            content: The new content value to set

        Note:
            The type of the firmware parameter remains unchanged. The content must be
            compatible with the existing parameter type.
        """
        self.value_obj.content = content

    def pb_copy(self, message: PB_ParameterSetRequest | PB_ParameterGetRequest) -> None:
        """Copy values to Protobuf message"""
        message.key_hash = hash(self)

        if isinstance(message, PB_ParameterSetRequest):
            setattr(message.value, f"{self.value_obj.type}_value", self.value_obj.content)

    def pb_read(self, message: PB_ParameterSetResponse | PB_ParameterGetResponse) -> None:
        """Read values from Protobuf message and update firmware parameter content.

        Args:
            message: The ParameterSetResponse or ParameterGetResponse containing the value to read

        Raises:
            ValueError: If the key_hash doesn't match the firmware parameter name or no value set
            FirmwareParameterValidationFailed: If firmware parameter validation failed on the embedded side
            FirmwareParameterReadOnly: If firmware parameter is read-only on the embedded side
            FirmwareParameterNotFound: If firmware parameter not found on the embedded side
        """

        # Verify that the name matches
        if message.key_hash != hash(self):
            raise ValueError(f"Key hash mismatch: expected '{hash(self)}', got '{message.key_hash}'")

        if isinstance(message, PB_ParameterSetResponse):
            # Check status and raise appropriate exceptions
            match message.status:
                case PB_ParameterStatus.VALIDATION_FAILED:
                    raise FirmwareParameterValidationFailed(f"Firmware parameter '{self.name}' validation failed")
                case PB_ParameterStatus.NOT_FOUND:
                    raise FirmwareParameterNotFound(f"Firmware parameter '{self.name}' not found in registry")
                case PB_ParameterStatus.SUCCESS:
                    pass  # Operation succeeded, nothing to do
        elif isinstance(message, PB_ParameterGetResponse):
            # Get the name of the field defined in the oneof
            which_field = message.value.WhichOneof("value")

            if which_field is None:
                raise ValueError("No value set in ParameterGetResponse, firmware parameter not found")

            # Get the value of the active field
            content = getattr(message.value, which_field)

            # Update the firmware parameter content
            self.value_obj.content = content


class FirmwareParametersGroup(RootModel):
    """Container for a group of firmware parameters with name-based access.

    This class manages a collection of firmware parameters and provides convenient
    get/set methods using firmware parameter names.

    The model directly represents a list of FirmwareParameter objects.
    """

    root: Annotated[list[FirmwareParameter], Field(default_factory=list)]

    def model_post_init(self, __context) -> None:
        """Build index after initialization."""
        super().model_post_init(__context)
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Rebuild the internal index for firmware parameter name lookup."""
        self._index: dict[str, int] = {param.name: idx for idx, param in enumerate(self.root)}

    def get(self, name: str) -> FirmwareParameter:
        """Get a firmware parameter by its name.

        Args:
            name: The firmware parameter name

        Returns:
            The FirmwareParameter object

        Raises:
            KeyError: If the firmware parameter name is not found
        """
        if name not in self._index:
            raise KeyError(f"Firmware parameter '{name}' not found")
        return self.root[self._index[name]]

    def __contains__(self, name: str) -> bool:
        """Check if a firmware parameter name exists in the list.

        Args:
            name: The firmware parameter name to check

        Returns:
            True if the firmware parameter exists, False otherwise
        """
        return name in self._index

    def __getitem__(self, name: str) -> float | int | bool:
        """Get a firmware parameter's value using bracket notation.

        Args:
            name: The firmware parameter name

        Returns:
            The firmware parameter's content value

        Raises:
            KeyError: If the firmware parameter name is not found
        """
        return self.get(name).value

    def __setitem__(self, name: str, value: float | int | bool) -> None:
        """Set a firmware parameter's value using bracket notation.

        Args:
            name: The firmware parameter name
            value: The new content value

        Raises:
            KeyError: If the firmware parameter name is not found
        """
        self.get(name).value = value

    def __len__(self) -> int:
        """Return the number of firmware parameters in the list."""
        return len(self.root)

    def __iter__(self):
        """Iterate over all firmware parameters."""
        return iter(self.root)
