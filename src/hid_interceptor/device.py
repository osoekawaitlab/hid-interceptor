"""HID device domain model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypedDict

from typing_extensions import Self

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from hid_interceptor.models import InputEvent


class RawInputEvent(TypedDict):
    """Raw input event data from a device."""

    sec: int
    usec: int
    type: int
    code: int
    value: int


class Device(ABC):
    """Abstract domain model for HID input devices.

    This represents a HID device from the application's perspective,
    providing a clean interface independent of the underlying library.
    """

    @classmethod
    @abstractmethod
    async def open(cls, path: str) -> Self:
        """Open and exclusively grab an input device.

        Args:
            path: Path to the input device (e.g., /dev/input/event0)

        Returns:
            A new device instance.
        """

    @property
    @abstractmethod
    def path(self) -> str:
        """Get the device path (e.g., /dev/input/event0).

        Returns:
            The device file path
        """

    @abstractmethod
    def events(self) -> AsyncIterator[InputEvent]:
        """Read, convert, and yield domain events from the device."""

    @abstractmethod
    def close(self) -> None:
        """Close and release the device.

        Releases the exclusive grab and closes the device file.
        Safe to call multiple times.
        """
