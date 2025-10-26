"""Main HIDInterceptor class for orchestrating the interception process."""

import asyncio
import logging

from evdev import list_devices

from hid_interceptor.device import Device
from hid_interceptor.evdev_device import EvdevDevice
from hid_interceptor.event_dispatcher import EventDispatcher, HookFn
from hid_interceptor.exceptions import DeviceOpenError

logger = logging.getLogger(__name__)


class HIDInterceptor:
    """Main class for HID event interception.

    This class orchestrates the entire interception process:
    - Discovers and opens input devices.
    - Gathers events from all devices into a single stream.
    - Dispatches events to user-provided hooks.

    The user of this class is responsible for managing the asyncio event loop.
    """

    def __init__(
        self,
        hooks: list[HookFn] | None = None,
        dispatcher: EventDispatcher | None = None,
        device_class: type[Device] = EvdevDevice,
    ) -> None:
        """Initialize the HIDInterceptor.

        Args:
            hooks: Optional list of hook functions to process events.
            dispatcher: Optional event dispatcher (for testing).
            device_class: Optional device class (for testing).
        """
        self._dispatcher = dispatcher or EventDispatcher(hooks=hooks)
        self._device_class = device_class
        self._logger = logger

    async def run(self, stop_event: asyncio.Event) -> None:
        """Run the HID interception loop.

        Monitors for input events until a stop signal is received.

        Args:
            stop_event: An asyncio Event that signals when to stop monitoring.
        """
        self._logger.info("Starting HIDInterceptor monitoring")
        opened_devices: list[Device] = []

        try:
            # Discover and open devices
            for device_path in list_devices():
                try:
                    device = await self._device_class.open(device_path)
                    opened_devices.append(device)
                except DeviceOpenError as e:  # noqa: PERF203
                    self._logger.warning("Failed to open device %s: %s", device_path, e)

            if not opened_devices:
                self._logger.warning("No devices found or opened. Doing nothing.")
                return

            # Create a monitoring task for each device
            tasks = [
                asyncio.create_task(self._monitor_one_device(device))
                for device in opened_devices
            ]

            self._logger.info(
                "Monitoring %d device(s). Waiting for stop signal...", len(tasks)
            )

            try:
                # Wait for the stop signal
                await stop_event.wait()
            except asyncio.CancelledError:
                self._logger.info("Monitoring task cancelled - initiating cleanup...")

            self._logger.info("Stop signal received. Cleaning up...")

            # Cancel all monitoring tasks
            for task in tasks:
                task.cancel()

            # Wait for all tasks to complete their cancellation
            await asyncio.gather(*tasks, return_exceptions=True)

        finally:
            for device in opened_devices:
                device.close()
            self._logger.info("HIDInterceptor monitoring stopped")

    async def _monitor_one_device(self, device: Device) -> None:
        """Monitor a single device and dispatch its events."""
        try:
            async for event in device.events():
                await self._dispatcher.dispatch(event)
        except asyncio.CancelledError:
            # This is expected on shutdown
            self._logger.debug("Monitoring cancelled for device: %s", device.path)
        except Exception:
            self._logger.exception("Error monitoring device: %s", device.path)
