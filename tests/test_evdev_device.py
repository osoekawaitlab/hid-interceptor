"""Tests for the EvdevDevice class."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from evdev import InputDevice, ecodes
from pytest_mock import MockerFixture

from hid_interceptor.evdev_device import GRAB_MAX_RETRIES, EvdevDevice
from hid_interceptor.exceptions import DeviceOpenError
from hid_interceptor.models import KeyEvent

DEVICE_PATH = "/dev/input/event-test"


@pytest.fixture
def mock_input_device(mocker: MockerFixture) -> MagicMock:
    """Fixture that mocks the evdev.InputDevice class constructor."""
    mock_instance = MagicMock(spec=InputDevice)
    mock_instance.path = DEVICE_PATH
    return mocker.patch(
        "hid_interceptor.evdev_device.InputDevice", return_value=mock_instance
    )


@pytest.mark.asyncio
class TestEvdevDevice:
    """Test the EvdevDevice class."""

    async def test_open_success(self, mock_input_device: MagicMock) -> None:
        """Test the happy path for opening a device."""
        device = await EvdevDevice.open(DEVICE_PATH)

        assert isinstance(device, EvdevDevice)
        assert device.path == DEVICE_PATH
        mock_input_device.assert_called_once_with(DEVICE_PATH)
        mock_input_device.return_value.grab.assert_called_once()

    async def test_open_initial_os_error(self, mock_input_device: MagicMock) -> None:
        """Test that DeviceOpenError is raised if InputDevice fails."""
        mock_input_device.side_effect = OSError("Permission denied")

        with pytest.raises(DeviceOpenError, match="Failed to open device"):
            await EvdevDevice.open(DEVICE_PATH)

    async def test_open_grab_retries_and_succeeds(
        self, mock_input_device: MagicMock, mocker: MockerFixture
    ) -> None:
        """Test that the grab operation is retried on failure."""
        grab_failures = 2
        expected_grab_calls = 3

        mock_grab = mock_input_device.return_value.grab
        mock_grab.side_effect = [OSError("Busy")] * grab_failures + [None]
        mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        await EvdevDevice.open(DEVICE_PATH)

        assert mock_grab.call_count == expected_grab_calls
        assert mock_sleep.call_count == grab_failures

    async def test_open_grab_fails_after_retries(
        self, mock_input_device: MagicMock, mocker: MockerFixture
    ) -> None:
        """Test that DeviceOpenError is raised after all grab retries fail."""
        mock_grab = mock_input_device.return_value.grab
        mock_grab.side_effect = OSError("Device permanently busy")
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        with pytest.raises(DeviceOpenError, match="Failed to grab device"):
            await EvdevDevice.open(DEVICE_PATH)

        assert mock_grab.call_count == GRAB_MAX_RETRIES
        # Check that the device was cleaned up
        mock_input_device.return_value.close.assert_called_once()

    async def test_events_generator(self, mock_input_device: MagicMock) -> None:
        """Test that the events generator reads, converts, and yields events."""
        mock_evdev_event = MagicMock()
        mock_evdev_event.sec = 123
        mock_evdev_event.usec = 456
        mock_evdev_event.type = ecodes.EV_KEY
        mock_evdev_event.code = ecodes.KEY_A
        mock_evdev_event.value = 1

        async def mock_read_loop() -> AsyncGenerator[MagicMock, None]:
            yield mock_evdev_event

        mock_input_device.return_value.async_read_loop = mock_read_loop

        device = await EvdevDevice.open(DEVICE_PATH)

        emitted_events = [event async for event in device.events()]

        assert len(emitted_events) == 1
        event = emitted_events[0]
        assert isinstance(event, KeyEvent)
        assert event.code == ecodes.KEY_A
        assert event.value == 1
        assert event.device == DEVICE_PATH

    async def test_events_generator_skips_unknown(
        self, mock_input_device: MagicMock
    ) -> None:
        """Test that the events generator skips unknown event types."""
        mock_evdev_event = MagicMock()
        mock_evdev_event.sec, mock_evdev_event.usec = 0, 0
        mock_evdev_event.type, mock_evdev_event.code, mock_evdev_event.value = (
            99,
            99,
            99,
        )

        async def mock_read_loop() -> AsyncGenerator[MagicMock, None]:
            yield mock_evdev_event

        mock_input_device.return_value.async_read_loop = mock_read_loop
        device = await EvdevDevice.open(DEVICE_PATH)

        emitted_events = [event async for event in device.events()]

        assert len(emitted_events) == 0

    async def test_close(self, mock_input_device: MagicMock) -> None:
        """Test that close() calls the underlying device methods."""
        device = await EvdevDevice.open(DEVICE_PATH)
        device.close()

        mock_input_device.return_value.ungrab.assert_called_once()
        mock_input_device.return_value.close.assert_called_once()
