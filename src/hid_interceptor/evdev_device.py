"""Evdev-based implementation of the Device domain model."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any

from evdev import InputDevice
from typing_extensions import Self

from hid_interceptor.device import Device, RawInputEvent
from hid_interceptor.exceptions import DeviceOpenError
from hid_interceptor.models import InputEvent, convert_raw_event

logger = logging.getLogger(__name__)

GRAB_RETRY_INTERVAL_SEC = 0.5
GRAB_MAX_RETRIES = 10


class EvdevDevice(Device):
    """An `evdev`-based HID device.

    This class is a concrete implementation of the `Device` abstract base class.
    It handles opening, grabbing, and reading events from a Linux `evdev` device.
    """

    def __init__(self, path: str, input_device: InputDevice[Any]) -> None:
        """Initialize the device. Private, use `open()` instead."""
        self._path = path
        self._device = input_device

    @classmethod
    async def open(cls, path: str) -> Self:
        """Open and exclusively grab an input device.

        This factory method handles the entire setup process for a device,
        including opening the file, grabbing it with retry logic, and returning
        a fully initialized `EvdevDevice` instance.

        Args:
            path: Path to the input device (e.g., /dev/input/event0)

        Returns:
            A new `EvdevDevice` instance.

        Raises:
            DeviceOpenError: If the device cannot be opened or grabbed.
        """
        try:
            input_device = InputDevice(path)
        except OSError as e:
            msg = f"Failed to open device {path}"
            raise DeviceOpenError(msg) from e

        # Retry grab with configurable max retries
        for attempt in range(GRAB_MAX_RETRIES):
            try:
                input_device.grab()
                logger.info("Successfully grabbed device: %s", path)
                break
            except OSError as e:
                if attempt == GRAB_MAX_RETRIES - 1:
                    msg = (
                        f"Failed to grab device {path} after {GRAB_MAX_RETRIES} "
                        "attempts"
                    )
                    # Clean up the opened device before raising
                    input_device.close()
                    raise DeviceOpenError(msg) from e
                logger.debug(
                    "Grab failed for %s (attempt %d/%d), retrying: %s",
                    path,
                    attempt + 1,
                    GRAB_MAX_RETRIES,
                    e,
                )
                await asyncio.sleep(GRAB_RETRY_INTERVAL_SEC)

        return cls(path, input_device)

    @property
    def path(self) -> str:
        """Get the device path (e.g., /dev/input/event0)."""
        return self._path

    async def events(self) -> AsyncIterator[InputEvent]:
        """Read, convert, and yield domain events from the device."""
        async for event in self._device.async_read_loop():
            raw_event: RawInputEvent = {
                "sec": event.sec,
                "usec": event.usec,
                "type": event.type,
                "code": event.code,
                "value": event.value,
            }
            domain_event = convert_raw_event(raw_event, self.path)
            if domain_event is not None:
                yield domain_event

    def close(self) -> None:
        """Close and release the device."""
        with contextlib.suppress(OSError):
            self._device.ungrab()

        with contextlib.suppress(OSError):
            self._device.close()
