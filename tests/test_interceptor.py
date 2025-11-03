"""Tests for the main HIDInterceptor class."""

import asyncio
import contextlib
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from hid_interceptor.device import Device
from hid_interceptor.event_dispatcher import EventDispatcher
from hid_interceptor.exceptions import DeviceOpenError
from hid_interceptor.interceptor import HIDInterceptor
from hid_interceptor.models import InputEvent, KeyEvent


@pytest.fixture
def mock_list_devices(mocker: MockerFixture) -> MagicMock:
    """Fixture that mocks evdev.list_devices."""
    return mocker.patch("hid_interceptor.interceptor.list_devices")


@pytest.fixture
def mock_device_class() -> MagicMock:
    """Fixture that mocks the Device class (e.g., EvdevDevice)."""
    mock_device = MagicMock(spec=Device)
    mock_device.path = "/dev/input/event-test"

    async def mock_events() -> AsyncGenerator[InputEvent, None]:
        yield MagicMock(spec=KeyEvent)

    mock_device.events = mock_events

    mock_class = MagicMock()
    mock_class.open = AsyncMock(return_value=mock_device)
    return mock_class


class TestHIDInterceptor:
    """Test the refactored HIDInterceptor class."""

    def test_init(self) -> None:
        """Test constructor with default and custom components."""
        # Default dispatcher
        interceptor = HIDInterceptor()
        assert isinstance(interceptor._dispatcher, EventDispatcher)

        # Custom dispatcher
        mock_dispatcher = MagicMock(spec=EventDispatcher)
        interceptor = HIDInterceptor(dispatcher=mock_dispatcher)
        assert interceptor._dispatcher is mock_dispatcher

    @pytest.mark.asyncio
    async def test_run_happy_path(
        self,
        mock_list_devices: MagicMock,
        mock_device_class: MagicMock,
        mocker: MockerFixture,
    ) -> None:
        """Test the full, successful lifecycle of the run method."""
        mock_list_devices.return_value = ["/dev/input/event0"]
        mock_dispatcher = MagicMock(spec=EventDispatcher)
        mock_dispatcher.dispatch = AsyncMock()

        interceptor = HIDInterceptor(
            dispatcher=mock_dispatcher, device_class=mock_device_class
        )
        stop_event = asyncio.Event()

        # Run the interceptor in a background task
        run_task = asyncio.create_task(interceptor.run(stop_event))
        await asyncio.sleep(0)  # Allow the task to start

        # Signal stop and wait for completion
        stop_event.set()
        await run_task

        # Assertions
        mock_list_devices.assert_called_once()
        mock_device_class.open.assert_awaited_once_with("/dev/input/event0")
        mock_dispatcher.dispatch.assert_awaited_once()

        # Check that the opened device was closed
        opened_device = mock_device_class.open.return_value
        opened_device.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_no_devices_found(self, mock_list_devices: MagicMock) -> None:
        """Test that run exits gracefully if no devices are found."""
        mock_list_devices.return_value = []
        interceptor = HIDInterceptor()
        stop_event = asyncio.Event()

        # This should complete without waiting for the stop_event
        await interceptor.run(stop_event)

        # No devices should be opened
        assert not stop_event.is_set()

    @pytest.mark.asyncio
    async def test_run_handles_device_open_error(
        self, mock_list_devices: MagicMock, mock_device_class: MagicMock
    ) -> None:
        """Test that a DeviceOpenError is handled gracefully."""
        mock_list_devices.return_value = ["/dev/input/event0"]
        mock_device_class.open.side_effect = DeviceOpenError("Test open error")

        interceptor = HIDInterceptor(device_class=mock_device_class)
        stop_event = asyncio.Event()

        # Should not raise an exception
        await interceptor.run(stop_event)

        mock_device_class.open.assert_awaited_once_with("/dev/input/event0")

    @pytest.mark.asyncio
    async def test_run_handles_monitoring_error(
        self, mock_list_devices: MagicMock, mock_device_class: MagicMock
    ) -> None:
        """Test that an error during event monitoring is handled."""
        mock_list_devices.return_value = ["/dev/input/event0"]
        mock_device = mock_device_class.open.return_value

        # Create a mock async iterator that raises an error
        mock_iterator = MagicMock()
        mock_iterator.__aiter__.return_value = mock_iterator
        mock_iterator.__anext__.side_effect = RuntimeError("Monitoring failed")
        mock_device.events.return_value = mock_iterator

        interceptor = HIDInterceptor(device_class=mock_device_class)
        stop_event = asyncio.Event()

        # Run and stop
        run_task = asyncio.create_task(interceptor.run(stop_event))
        await asyncio.sleep(0)
        stop_event.set()
        await run_task

        # Assert cleanup still happened
        mock_device.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_handles_cancelled_error(
        self, mock_list_devices: MagicMock, mock_device_class: MagicMock
    ) -> None:
        """Test that CancelledError during stop_event.wait() is handled gracefully."""
        mock_list_devices.return_value = ["/dev/input/event0"]
        mock_dispatcher = MagicMock(spec=EventDispatcher)
        mock_dispatcher.dispatch = AsyncMock()

        interceptor = HIDInterceptor(
            dispatcher=mock_dispatcher, device_class=mock_device_class
        )
        stop_event = asyncio.Event()

        # Create a task and cancel it while it's waiting on stop_event
        run_task = asyncio.create_task(interceptor.run(stop_event))
        await asyncio.sleep(0)  # Allow the task to reach stop_event.wait()

        # Cancel the task
        run_task.cancel()

        # This should handle CancelledError gracefully in run()
        # If run() properly propagates CancelledError, we suppress it here
        with contextlib.suppress(asyncio.CancelledError):
            await run_task

        # Assert cleanup still happened
        opened_device = mock_device_class.open.return_value
        opened_device.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_sets_ready_event(
        self, mock_list_devices: MagicMock, mock_device_class: MagicMock
    ) -> None:
        """Test that ready_event is set when monitoring starts successfully."""
        mock_list_devices.return_value = ["/dev/input/event0"]
        mock_dispatcher = MagicMock(spec=EventDispatcher)
        mock_dispatcher.dispatch = AsyncMock()

        interceptor = HIDInterceptor(
            dispatcher=mock_dispatcher, device_class=mock_device_class
        )
        stop_event = asyncio.Event()
        ready_event = asyncio.Event()

        # Run the interceptor in a background task
        run_task = asyncio.create_task(interceptor.run(stop_event, ready_event))
        await asyncio.sleep(0)  # Allow the task to start

        # Wait for ready_event to be set
        await asyncio.wait_for(ready_event.wait(), timeout=1.0)
        assert ready_event.is_set()

        # Signal stop and wait for completion
        stop_event.set()
        await run_task

    @pytest.mark.asyncio
    async def test_run_does_not_set_ready_event_when_no_devices(
        self, mock_list_devices: MagicMock
    ) -> None:
        """Test that ready_event is NOT set when no devices are found."""
        mock_list_devices.return_value = []
        interceptor = HIDInterceptor()
        stop_event = asyncio.Event()
        ready_event = asyncio.Event()

        # This should complete without setting ready_event
        await interceptor.run(stop_event, ready_event)

        # ready_event should not be set
        assert not ready_event.is_set()

    @pytest.mark.asyncio
    async def test_run_works_without_ready_event(
        self, mock_list_devices: MagicMock, mock_device_class: MagicMock
    ) -> None:
        """Test that run works normally when ready_event is not provided."""
        mock_list_devices.return_value = ["/dev/input/event0"]
        mock_dispatcher = MagicMock(spec=EventDispatcher)
        mock_dispatcher.dispatch = AsyncMock()

        interceptor = HIDInterceptor(
            dispatcher=mock_dispatcher, device_class=mock_device_class
        )
        stop_event = asyncio.Event()

        # Run without ready_event (should not raise)
        run_task = asyncio.create_task(interceptor.run(stop_event))
        await asyncio.sleep(0)

        # Signal stop and wait for completion
        stop_event.set()
        await run_task

        # Verify it ran successfully
        mock_device_class.open.assert_awaited_once()
